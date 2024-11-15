from influxdb_client import InfluxDBClient

import numpy as np


# InfluxDB mio (in locale) #

org = "iotorg"
bucket = "iotdb"
token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
influx_IP = "http://localhost:8086"

topicInflux_temperatura = "temperature"

query = 'from(bucket: "' + bucket + '")' \
        '|> range(start: -1h)' \
        '|> filter(fn: (r) => r._measurement == "' + topicInflux_temperatura + '")'

# Establish a connection
client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)

# Instantiate the WriteAPI and QueryAPI
query_api = client_influx.query_api()


# Return the table and print the result
result = query_api.query(org=org, query=query)
results = []
for table in result:
    for record in table.records:
        results.append((record.get_value(), record.get_field()))
#print(results)
print()

filtered = filter(lambda data: data[1]=="outdoor", results)
filtered = list(filtered)
print(filtered)
print()

values = [list(i)[0] for i in filtered] # list of lists
values = values[-20:]       # Ultimi 10 elementi della lista
print(values)

# La varianza di una variabile statistica fornisce una misura della variabilita' dei valori assunti dalla variabile stessa
print(np.var(values))