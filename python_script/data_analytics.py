from influxdb_client import InfluxDBClient, Point      # InfluxDB

import numpy as np
import time
import datetime

# FB Prophet
import pandas as pd
from prophet import Prophet

import paho.mqtt.publish as publish     # MQTT



# Topic #

# InfluxDB
topicInflux_temperatura = "temperature"
topicInflux_allarme = "alarm"
topicInflux_forecastIndoor = "forecast_indoor"
topicInflux_forecastOutdoor = "forecast_outdoor"

topicMqtt_allarme = "alarm_led"     # MQTT


# InfluxDB mio (in locale) #

org = "iotorg"
bucket = "iotdb"
token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
influx_IP = "http://localhost:8086"

# Establish a connection
client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)

# Instantiate the WriteAPI and QueryAPI
query_api = client_influx.query_api()
write_api = client_influx.write_api()



# Forecast #


# Query di tutte le temperature presenti sul DB
#freqDataAggregation = "10m"
query_allTemperatures = 'from(bucket: "' + bucket + '")' \
                        '|> range(start: 2024-11-19T15:33:00Z)' \
                        '|> filter(fn: (r) => r._measurement == "' + topicInflux_temperatura + '")' #\
                        #'|> aggregateWindow(every: ' + freqDataAggregation + ', fn: mean)'

results = query_api.query(org=org, query=query_allTemperatures)        # Return the table of all the temperatures
print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Temperature data (all) received from database InfluxDB\n")

datetimeValues_allIndoorTemperatures = []
datetimeValues_allOutdoorTemperatures = []
for table in results:
    for record in table.records:
        if record.get_field() == "indoor":
            datetimeValues_allIndoorTemperatures.append((record.get_time().astimezone().strftime('%Y-%m-%d %H:%M:%S'), record.get_value()))       # .astimezone(): converte l'orario nell'UTC di Roma
        elif record.get_field() == "outdoor":
            datetimeValues_allOutdoorTemperatures.append((record.get_time().astimezone().strftime('%Y-%m-%d %H:%M:%S'), record.get_value()))       # .astimezone(): converte l'orario nell'UTC di Roma


# FB Prophet #

df_allIndoorTemperatures = pd.DataFrame(datetimeValues_allIndoorTemperatures, columns = ['ds', 'y'])
df_allOutdoorTemperatures = pd.DataFrame(datetimeValues_allOutdoorTemperatures, columns = ['ds', 'y'])
print("ALL indoor temperatures:")
print(df_allIndoorTemperatures)
print()
print("ALL outdoor temperatures:")
print(df_allOutdoorTemperatures)
print()

model_indoor = Prophet()
model_outdoor = Prophet()
model_indoor.fit(df_allIndoorTemperatures)
model_outdoor.fit(df_allOutdoorTemperatures)

#freqForecast = "10min"      # Ogni quanto tempo
freqForecast = "1min"      # Ogni quanto tempo
timesForecast = 6           # Quante volte
future_indoor = model_indoor.make_future_dataframe(periods=timesForecast, freq=freqForecast)
future_outdoor = model_outdoor.make_future_dataframe(periods=timesForecast, freq=freqForecast)

forecast_indoor = model_indoor.predict(future_indoor)
forecast_outdoor = model_outdoor.predict(future_outdoor)
print("FORECAST indoor temperature:")
print(forecast_indoor[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(timesForecast))
print()
print("FORECAST outdoor temperature:")
print(forecast_outdoor[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(timesForecast))
print()

plot_indoor = model_indoor.plot(forecast_indoor)
plot_outdoor = model_outdoor.plot(forecast_outdoor)
plot_indoor.savefig("forecast_indoorTemperatures.svg")
plot_outdoor.savefig("forecast_outdoorTemperatures.svg")
print("Forecast plot saved locally")

plotComponents_indoor = model_indoor.plot_components(forecast_indoor)
plotComponents_outdoor = model_outdoor.plot_components(forecast_outdoor)
#plotComponents_indoor.savefig("forecastComponents_indoorTemperatures.svg")
#plotComponents_outdoor.savefig("forecastComponents_outdoorTemperatures.svg")



# Recupero ciclicamente i dati dal DB e li analizzo per controllare un'eventuale dispersione di calore #


# Query delle temperature rilevate negli ultimi minuti
lastMinutes = '2'
query_lastTemperatures =    'from(bucket: "' + bucket + '")' \
                            '|> range(start: -' + lastMinutes + 'm)' \
                            '|> filter(fn: (r) => r._measurement == "' + topicInflux_temperatura + '")'

allarmeAttivato = False

# Forecast
forecast_indoor = forecast_indoor[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(timesForecast).reset_index(drop=True)
forecast_outdoor = forecast_outdoor[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(timesForecast).reset_index(drop=True)
index_forecastIndoor = 0
index_forecastOutdoor = 0


while True:

    print("\n\n***\n\n")


    results = query_api.query(org=org, query=query_lastTemperatures)        # Return the table of the temperatures
    print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Temperature data (of last " + lastMinutes + " minutes) received from database InfluxDB\n")

    lastIndoorTemperatures = []
    lastOutdoorTemperatures = []
    for table in results:
        for record in table.records:
            if record.get_field() == "indoor":
                lastIndoorTemperatures.append(record.get_value())
            elif record.get_field() == "outdoor":
                lastOutdoorTemperatures.append(record.get_value())

    print("Last indoor temperatures:")
    print(lastIndoorTemperatures)
    #print(np.var(lastIndoorTemperatures))       # Varianza
    #print(np.mean(lastIndoorTemperatures))      # Media
    print()

    print("Last outdoor temperatures:")
    print(lastOutdoorTemperatures)
    #print(np.var(lastOutdoorTemperatures))      # Varianza
    #print(np.mean(lastOutdoorTemperatures))     # Media
    print("\n")


    # Controllo un'eventuale dispersione di calore (identificata tramite rapidi cambiamenti di temperatura) #

    sogliaVarianza = 0.01       # Una temperatura costante (in rapido cambiamento) ha una varianza minore (maggiore) di questo valore

    minTemperaturaIniziale = min(lastIndoorTemperatures[0], lastOutdoorTemperatures[0])
    maxTemperaturaIniziale = max(lastIndoorTemperatures[0], lastOutdoorTemperatures[0])

    # La varianza di una variabile statistica fornisce una misura della variabilita' dei valori assunti dalla variabile stessa
    if ((   np.var(lastOutdoorTemperatures) < sogliaVarianza <= np.var(lastIndoorTemperatures)              # Se la temperatura interna ha un cambiamento rapido e quella esterna e' costante...
            and minTemperaturaIniziale < np.mean(lastIndoorTemperatures) < maxTemperaturaIniziale)          # ... e le due temperature si stanno avvicinando
        or (np.var(lastIndoorTemperatures) < sogliaVarianza <= np.var(lastOutdoorTemperatures)              # (oppure viceversa)
            and minTemperaturaIniziale < np.mean(lastOutdoorTemperatures) < maxTemperaturaIniziale)):

        print("-----------------------------")
        print(" ALARM: HVAC waste detected!")
        print("-----------------------------")


        if not allarmeAttivato:     # Viene eseguito solo alla prima avvisaglia, poi aspetta di tornare a una situazione di normalita'

            allarmeAttivato = True


            # Memorizzo l'evento di allarme su InfluxDB #

            # Create and write the point
            p_alarm = Point(topicInflux_allarme).field("waste", 1)
            write_api.write(bucket=bucket, org=org, record=p_alarm)
            print("Alarm event stored on database InfluxDB")


            # Accende il led di allarme sull'ESP (1 = true)
            publish.single(topicMqtt_allarme, 1, hostname="localhost")      # MQTT
            print("[MQTT]  Sent message to turn on the alarm led")

    else:

        print("Temperature data processed successfully")

        if allarmeAttivato:

            allarmeAttivato = False

            # Spegne il led di allarme sull'ESP (0 = false)
            publish.single(topicMqtt_allarme, 0, hostname="localhost")      # MQTT
            print("[MQTT]  Sent message to turn off the alarm led")
    print()


    # Inserisco i valori del forecast su InfluxDB (man mano che quell'orario viene raggiunto) #

    fieldInflux_yhat = "yhat"
    fieldInflux_yhatLow = "yhat_lower"
    fieldInflux_yhatUp = "yhat_upper"

    # Indoor
    if (index_forecastIndoor < timesForecast
        and datetime.datetime.now() > forecast_indoor['ds'].loc[index_forecastIndoor]):

        # Create and write the points #

        p_forecastIndoor_yhat = Point(topicInflux_forecastIndoor).field(fieldInflux_yhat, forecast_indoor[fieldInflux_yhat].loc[index_forecastIndoor])
        p_forecastIndoor_yhatLow = Point(topicInflux_forecastIndoor).field(fieldInflux_yhatLow, forecast_indoor[fieldInflux_yhatLow].loc[index_forecastIndoor])
        p_forecastIndoor_yhatUp = Point(topicInflux_forecastIndoor).field(fieldInflux_yhatUp, forecast_indoor[fieldInflux_yhatUp].loc[index_forecastIndoor])

        write_api.write(bucket=bucket, org=org, record=p_forecastIndoor_yhat)
        write_api.write(bucket=bucket, org=org, record=p_forecastIndoor_yhatLow)
        write_api.write(bucket=bucket, org=org, record=p_forecastIndoor_yhatUp)

        print("Forecasted indoor temperature values stored on database InfluxDB")


        index_forecastIndoor = index_forecastIndoor + 1

    # Outdoor
    if (index_forecastOutdoor < timesForecast
        and datetime.datetime.now() > forecast_outdoor['ds'].loc[index_forecastOutdoor]):

        # Create and write the points #

        p_forecastOutdoor_yhat = Point(topicInflux_forecastOutdoor).field(fieldInflux_yhat, forecast_outdoor[fieldInflux_yhat].loc[index_forecastOutdoor])
        p_forecastOutdoor_yhatLow = Point(topicInflux_forecastOutdoor).field(fieldInflux_yhatLow, forecast_outdoor[fieldInflux_yhatLow].loc[index_forecastOutdoor])
        p_forecastOutdoor_yhatUp = Point(topicInflux_forecastOutdoor).field(fieldInflux_yhatUp, forecast_outdoor[fieldInflux_yhatUp].loc[index_forecastOutdoor])

        write_api.write(bucket=bucket, org=org, record=p_forecastOutdoor_yhat)
        write_api.write(bucket=bucket, org=org, record=p_forecastOutdoor_yhatLow)
        write_api.write(bucket=bucket, org=org, record=p_forecastOutdoor_yhatUp)

        print("Forecasted outdoor temperature values stored on database InfluxDB")


        index_forecastOutdoor = index_forecastOutdoor + 1
    print()


    waitSec = 30
    print("\n\nWaiting " + str(waitSec) + " seconds...")
    time.sleep(waitSec)