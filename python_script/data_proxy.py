import logging
import asyncio
import time
import datetime

from pickle import GET
from aiocoap import *                                   # CoAP

import paho.mqtt.publish as publish                     # MQTT

from influxdb_client import InfluxDBClient, Point       # InfluxDB



logging.basicConfig(level=logging.INFO)

async def main():

    ip_coap_server = "192.168.150.4"    # Indirizzo IP dell'ESP


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

    client_influx = InfluxDBClient(url=influx_IP, token=token, org=org)         # Establish a connection
    write_api = client_influx.write_api()                                       # Instantiate the WriteAPI



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

    # Evaluation (latency)
    sommaValoriLatenza = 0      # Somma delle latenze
    numValoriLatenza = 0        # Quanti valori ho sommato (per il calcolo della media)
    minLatenza = 0              # Latenza minima
    maxLatenza = 0              # Latenza massima
    startTime = datetime.datetime.now()
    evalutationLatencyDone = False

    while True:

        # Chiedo i valori delle temperature al server ESP #


        # Interna #

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaInterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaInterna)

        print("[%s, CoAP]  Sending GET request for endpoint %s...\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaInterna))

        try:
            # Wait until the response is ready
            datetimeStart_interna = datetime.datetime.now()
            response_temperaturaInterna = await protocol.request(req_temperaturaInterna).response
            datetimeStop_interna = datetime.datetime.now()
        except Exception as e:
            print("[CoAP]  Failed to fetch resource for endpoint " + topicCoap_temperaturaInterna + ":")
            print(e)
            print()
        else:
            response_temperaturaInterna_value = float(response_temperaturaInterna.payload.decode("utf-8"))


            # Evaluation (latency) #

            millisLatenzaCorrente_temperaturaInterna = (datetimeStop_interna - datetimeStart_interna).total_seconds() * 1000

            sommaValoriLatenza = sommaValoriLatenza + millisLatenzaCorrente_temperaturaInterna
            numValoriLatenza = numValoriLatenza + 1
            if minLatenza == 0 and maxLatenza == 0:
                minLatenza = millisLatenzaCorrente_temperaturaInterna
                maxLatenza = millisLatenzaCorrente_temperaturaInterna
            elif millisLatenzaCorrente_temperaturaInterna < minLatenza:
                minLatenza = millisLatenzaCorrente_temperaturaInterna
            elif millisLatenzaCorrente_temperaturaInterna > maxLatenza:
                maxLatenza = millisLatenzaCorrente_temperaturaInterna


            print("[%s, CoAP]  RESULT for endpoint %s:\n(%s, %d millis)  %0.2f" % (datetimeStop_interna.strftime('%H:%M:%S'), topicCoap_temperaturaInterna, response_temperaturaInterna.code, millisLatenzaCorrente_temperaturaInterna, response_temperaturaInterna_value))        # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)


            # InfluxDB #
            # Create and write the point
            p = Point(topicInflux_temperatura).field("indoor", response_temperaturaInterna_value)
            write_api.write(bucket=bucket, org=org, record=p)
            print("Temperature value stored on database InfluxDB\n")


        # Esterna #

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaEsterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaEsterna)

        print("[%s, CoAP]  Sending GET request for endpoint %s...\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaEsterna))

        try:
            # Wait until the response is ready
            datetimeStart_esterna = datetime.datetime.now()
            response_temperaturaEsterna = await protocol.request(req_temperaturaEsterna).response
            datetimeStop_esterna = datetime.datetime.now()
        except Exception as e:
            print("[CoAP]  Failed to fetch resource for endpoint " + topicCoap_temperaturaEsterna + ":")
            print(e)
            print()
        else:
            response_temperaturaEsterna_value = float(response_temperaturaEsterna.payload.decode("utf-8"))


            # Evaluation (latency) #

            millisLatenzaCorrente_temperaturaEsterna = (datetimeStop_esterna - datetimeStart_esterna).total_seconds() * 1000

            sommaValoriLatenza = sommaValoriLatenza + millisLatenzaCorrente_temperaturaEsterna
            numValoriLatenza = numValoriLatenza + 1
            if minLatenza == 0 and maxLatenza == 0:
                minLatenza = millisLatenzaCorrente_temperaturaEsterna
                maxLatenza = millisLatenzaCorrente_temperaturaEsterna
            elif millisLatenzaCorrente_temperaturaEsterna < minLatenza:
                minLatenza = millisLatenzaCorrente_temperaturaEsterna
            elif millisLatenzaCorrente_temperaturaEsterna > maxLatenza:
                maxLatenza = millisLatenzaCorrente_temperaturaEsterna


            print("[%s, CoAP]  RESULT for endpoint %s:\n(%s, %d millis)  %0.2f" % (datetimeStop_esterna.strftime('%H:%M:%S'), topicCoap_temperaturaEsterna, response_temperaturaEsterna.code, millisLatenzaCorrente_temperaturaEsterna, response_temperaturaEsterna_value))        # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)


            # InfluxDB #
            # Create and write the point
            p = Point(topicInflux_temperatura).field("outdoor", response_temperaturaEsterna_value)
            write_api.write(bucket=bucket, org=org, record=p)
            print("Temperature value stored on database InfluxDB\n")


        # Evaluation (latency)
        currentTime = datetime.datetime.now()
        if ((not evalutationLatencyDone)
            and ((currentTime - startTime).total_seconds() > 3600)):        # Se e' passata un'ora dall'inizio
            print("[%s]  EVALUATION - Mean latency (of last hour):   %d millis  [%d, %d]\n" % (currentTime.strftime('%H:%M:%S'), sommaValoriLatenza / numValoriLatenza, minLatenza, maxLatenza))
            evalutationLatencyDone = True


        waitSec = 5
        print("Waiting " + str(waitSec) + " seconds...\n")
        time.sleep(waitSec)

if __name__ == "__main__":
        asyncio.run(main())
