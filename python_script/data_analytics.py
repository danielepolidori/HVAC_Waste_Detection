from influxdb_client import InfluxDBClient

import numpy as np


# InfluxDB mio (in locale) #

org = "iotorg"
bucket = "iotdb"
token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
influx_IP = "http://localhost:8086"

topicInflux_temperatura = "temperature"

query_allTemperatures = 'from(bucket: "' + bucket + '")' \
        '|> range(start: -1h)' \
        '|> filter(fn: (r) => r._measurement == "' + topicInflux_temperatura + '")'

# Establish a connection
client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)

# Instantiate the WriteAPI and QueryAPI
query_api = client_influx.query_api()



# Return the table and print the result
result = query_api.query(org=org, query=query_allTemperatures)
results = []
for table in result:
    for record in table.records:
        results.append((record.get_value(), record.get_field()))
#print(results)
print()


# Interna #

filtered_indoorTemperature = list(filter(lambda data: data[1]=="indoor", results))
#print(filtered_indoorTemperature)
print()

values_indoorTemperature = [list(i)[0] for i in filtered_indoorTemperature]     # list of lists
values_indoorTemperature = values_indoorTemperature[-20:]       # Ultimi 10 elementi della lista
print("indoor:")
print(values_indoorTemperature)

# La varianza di una variabile statistica fornisce una misura della variabilita' dei valori assunti dalla variabile stessa
varianza_indoorTemperature = np.var(values_indoorTemperature)
print(varianza_indoorTemperature)
print()


# Esterna #

filtered_outdoorTemperature = list(filter(lambda data: data[1]=="outdoor", results))
#print(filtered_outdoorTemperature)
print()

values_outdoorTemperature = [list(i)[0] for i in filtered_outdoorTemperature]     # list of lists
values_outdoorTemperature = values_outdoorTemperature[-20:]       # Ultimi 10 elementi della lista
print("outdoor:")
print(values_outdoorTemperature)

# La varianza di una variabile statistica fornisce una misura della variabilita' dei valori assunti dalla variabile stessa
varianza_outdoorTemperature = np.var(values_outdoorTemperature)
print(varianza_outdoorTemperature)
print()



# Controllo

differenzaInizialeTemperature = abs(values_indoorTemperature[0] - values_outdoorTemperature[0])
differenzaFinaleTemperature = abs(values_indoorTemperature[-1] - values_outdoorTemperature[-1])

if (((varianza_indoorTemperature > 0.2              # Se la temperatura interna ha un picco
    and varianza_outdoorTemperature < 0.05)         # e quella esterna e' costante...
    or (varianza_outdoorTemperature > 0.2           # (...oppure il contrario...)
    and varianza_indoorTemperature < 0.05))
    and differenzaFinaleTemperature < differenzaInizialeTemperature):       # ... e una temperatura si sta avvicinando all'altra

    print("ALARM!!!")