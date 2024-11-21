import logging
import asyncio
import time
import datetime

from pickle import GET
from aiocoap import *                   # CoAP

import paho.mqtt.publish as publish     # MQTT

from influxdb_client import InfluxDBClient, Point     # InfluxDB



logging.basicConfig(level=logging.INFO)

async def main():

    ip_coap_server = "192.168.62.4"    # Indirizzo IP dell'ESP


    # Topic #

    # CoAP
    topicCoap_temperaturaInterna = "indoor_temperature"
    topicCoap_temperaturaEsterna = "outdoor_temperature"

    # MQTT
    topicMqtt_readTemperaturaInterna = "read_indoor_dht"
    topicMqtt_samplingRateTemperaturaInterna = "sampling_rate_indoor_dht"
    topicMqtt_readTemperaturaEsterna = "read_outdoor_dht"
    topicMqtt_samplingRateTemperaturaEsterna = "sampling_rate_outdoor_dht"

    topicInflux_temperatura = "temperature"     # InfluxDB



    # InfluxDB mio (in locale) #

    org = "iotorg"
    bucket = "iotdb"
    token = "WovvdX_JQ1IQcXgW10JMleWYgazmWt9vYftJKeCX39fHuFvP2i0ElyqWju3ausXWemtwhgwKSp_MI54aa9Lz7g=="
    influx_IP = "http://localhost:8086"

    # Establish a connection
    client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)

    # Instantiate the WriteAPI and QueryAPI
    write_api = client_influx.write_api()



    # MQTT #

    # Attivo la lettura dei sensori dell'ESP e imposto il rispettivo sampling rate (localhost: Indirizzo IP del mio pc con mosquitto)

    # Interna
    publish.single(topicMqtt_readTemperaturaInterna, 1, hostname="localhost")               # Start sensor reading (1 = true)
    publish.single(topicMqtt_samplingRateTemperaturaInterna, 3000, hostname="localhost")    # Set sampling rate (millis)

    # Esterna
    publish.single(topicMqtt_readTemperaturaEsterna, 1, hostname="localhost")               # Start sensor reading (1 = true)
    publish.single(topicMqtt_samplingRateTemperaturaEsterna, 20000, hostname="localhost")   # Set sampling rate (millis)

    print("[" + datetime.datetime.now().strftime('%H:%M:%S') + ", MQTT]  Sent messages to start the sensors reading and to set each sampling rate\n")



    # CoAP #

    protocol = await Context.create_client_context()

    while True:

        # Chiedo i valori delle temperature al server ESP #


        # Interna #

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaInterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaInterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + ", CoAP]  Sending GET request for endpoint " + topicCoap_temperaturaInterna + "...\n")

        try:
            # Wait until the response is ready
            response_temperaturaInterna = await protocol.request(req_temperaturaInterna).response
        except Exception as e:
            print("[CoAP] Failed to fetch resource for endpoint " + topicCoap_temperaturaInterna + ":")
            print(e)
        else:
            #response_temperaturaInterna_value = float(response_temperaturaInterna.payload.decode("utf-8"))
            response_temperaturaInterna_value = float(response_temperaturaInterna.payload.decode("utf-8")) - 2.0    #tmp

            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s, CoAP]  RESULT for endpoint %s:\n(%s)  %0.2f" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaInterna, response_temperaturaInterna.code, response_temperaturaInterna_value))

            # InfluxDB #
            # Create and write the point
            p = Point(topicInflux_temperatura).field("indoor", response_temperaturaInterna_value)
            write_api.write(bucket=bucket, org=org, record=p)
            print("Data stored on database InfluxDB\n")


        # Esterna #

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaEsterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaEsterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + ", CoAP]  Sending GET request for endpoint " + topicCoap_temperaturaEsterna + "...\n")

        try:
            # Wait until the response is ready
            response_temperaturaEsterna = await protocol.request(req_temperaturaEsterna).response
        except Exception as e:
            print("[CoAP] Failed to fetch resource for endpoint " + topicCoap_temperaturaEsterna + ":")
            print(e)
        else:
            response_temperaturaEsterna_value = float(response_temperaturaEsterna.payload.decode("utf-8"))

            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s, CoAP]  RESULT for endpoint %s:\n(%s)  %0.2f" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaEsterna, response_temperaturaEsterna.code, response_temperaturaEsterna_value))

            # InfluxDB #
            # Create and write the point
            p = Point(topicInflux_temperatura).field("outdoor", response_temperaturaEsterna_value)
            write_api.write(bucket=bucket, org=org, record=p)
            print("Data stored on database InfluxDB\n")


        time.sleep(5)

if __name__ == "__main__":
        asyncio.run(main())
