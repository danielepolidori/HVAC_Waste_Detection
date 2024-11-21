from influxdb_client import InfluxDBClient      # InfluxDB

import numpy as np
import time
import datetime

# FB Prophet
import pandas as pd
from prophet import Prophet



# InfluxDB mio (in locale) #

org = "iotorg"
bucket = "iotdb"
token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
influx_IP = "http://localhost:8086"

topicInflux_temperatura = "temperature"

# Chiedo i valori di temperatura rilevati negli ultimi minuti (ho un nuovo elemento ogni 5 secondi)
lastMinutes = '2'
query_lastTemperatures =    'from(bucket: "' + bucket + '")' \
                            '|> range(start: -' + lastMinutes + 'm)' \
                            '|> filter(fn: (r) => r._measurement == "' + topicInflux_temperatura + '")'

# Establish a connection
client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)

# Instantiate the WriteAPI and QueryAPI
query_api = client_influx.query_api()



# Recupero ciclicamente i dati dal DB e li analizzo
while True:

    results = query_api.query(org=org, query=query_lastTemperatures)        # Return the table of all the temperatures
    print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "] Temperature data (of last " + lastMinutes + " minutes) received from database InfluxDB\n")

    lastIndoorTemperatures = []
    lastOutdoorTemperatures = []
    datetimeValues = []
    for table in results:
        for record in table.records:
            if record.get_field() == "indoor":
                lastIndoorTemperatures.append(record.get_value())
            elif record.get_field() == "outdoor":
                lastOutdoorTemperatures.append(record.get_value())
                datetimeValues.append((record.get_time().astimezone().strftime('%Y-%m-%d %H:%M:%S'), record.get_value()))       # .astimezone(): converte l'orario nell'UTC di Roma

    print("Indoor temperatures:")
    print(lastIndoorTemperatures)
    print(np.var(lastIndoorTemperatures))        # Varianza
    print()

    print("Outdoor temperatures:")
    print(lastOutdoorTemperatures)
    print(np.var(lastOutdoorTemperatures))       # Varianza
    print()
    print()



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
    else:
        print("Temperature data processed successfully")
    print()



    # FB Prophet

    #print(datetimeValues)
    print()

    df = pd.DataFrame(datetimeValues)
    df.columns = ['ds', 'y']
    print(df.tail())
    print()

    model = Prophet()
    #model = Prophet(interval_width=0.95)   # prof
    model.fit(df)

    future = model.make_future_dataframe(periods=60, freq='s')      # Prevede i futuri 60 secondi
    #print(future.tail())
    print()

    forecast = model.predict(future)
    print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
    print()

    fig1 = model.plot(forecast)
    #fig1 = model.plot(forecast, uncertainty=True)  # prof
    fig1.savefig("prophet_plot.svg")

    fig2 = model.plot_components(forecast)
    #fig2.savefig("prophet_plotComponents.svg")



    print()
    print("***")
    print()
    print()



    time.sleep(30)