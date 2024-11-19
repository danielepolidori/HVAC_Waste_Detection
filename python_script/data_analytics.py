from influxdb_client import InfluxDBClient

import numpy as np
import time
import datetime


# InfluxDB mio (in locale) #

org = "iotorg"
bucket = "iotdb"
token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
influx_IP = "http://localhost:8086"

topicInflux_temperatura = "temperature"

# Chiedo i valori di temperatura rilevati negli ultimi minuti (ho un nuovo elemento ogni 5 secondi)
lastMinutes = '2'
query_lastTemperatures = 'from(bucket: "' + bucket + '")' \
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
    for table in results:
        for record in table.records:
            if record.get_field() == "indoor":
                lastIndoorTemperatures.append(record.get_value())
            elif record.get_field() == "outdoor":
                lastOutdoorTemperatures.append(record.get_value())

    print("Indoor temperatures:")
    print(lastIndoorTemperatures)
    #print(np.var(lastIndoorTemperatures))        # Varianza
    print()

    print("Outdoor temperatures:")
    print(lastOutdoorTemperatures)
    #print(np.var(lastOutdoorTemperatures))       # Varianza
    print()
    print()



    # Controllo un'eventuale dispersione di calore (identificata tramite rapidi cambiamenti di temperatura) #

    varianza_costante = 0.05                # Una temperatura costante ha una varianza minore di questo valore
    varianza_cambiamentoRapido = 0.15        # Una temperatura in rapido cambiamento ha una varianza maggiore di questo valore

    minTemperaturaIniziale = min(lastIndoorTemperatures[0], lastOutdoorTemperatures[0])
    maxTemperaturaIniziale = max(lastIndoorTemperatures[0], lastOutdoorTemperatures[0])

    # La varianza di una variabile statistica fornisce una misura della variabilita' dei valori assunti dalla variabile stessa
    if ((np.var(lastIndoorTemperatures) > varianza_cambiamentoRapido                                # Se la temperatura interna ha un cambiamento rapido...
        and np.var(lastOutdoorTemperatures) < varianza_costante                                     # ...quella esterna e' costante...
        and minTemperaturaIniziale <= np.mean(lastIndoorTemperatures) <= maxTemperaturaIniziale)    # ... e le due temperature si stanno avvicinando
        or (np.var(lastOutdoorTemperatures) > varianza_cambiamentoRapido                            # (oppure viceversa)
        and np.var(lastIndoorTemperatures) < varianza_costante
        and minTemperaturaIniziale <= np.mean(lastOutdoorTemperatures) <= maxTemperaturaIniziale)):

        print("ALARM: HVAC waste detected!")
    else:
        print("Temperature data processed successfully")

    print()
    print()
    print("***")
    print()
    print()



    time.sleep(30)