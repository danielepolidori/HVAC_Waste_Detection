import logging
import asyncio
import time
import datetime

from pickle import GET
from aiocoap import *                   # CoAP

import paho.mqtt.publish as publish     # MQTT



logging.basicConfig(level=logging.INFO)

async def main():

    ip_coap_server = "192.168.241.4"    # Indirizzo IP dell'ESP


    # Topic CoAP
    topicCoap_temperaturaInterna = "temperatura_interna"
    topicCoap_temperaturaEsterna = "temperatura_esterna"


    # Topic MQTT

    topicMqtt_readTemperaturaInterna = "read_dht_interno"
    topicMqtt_samplingRateTemperaturaInterna = "sampling_rate_dht_interno"

    topicMqtt_readTemperaturaEsterna = "read_dht_esterno"
    topicMqtt_samplingRateTemperaturaEsterna = "sampling_rate_dht_esterno"



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


        # Interna

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaInterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaInterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + ", CoAP]  Sending GET request for endpoint '" + topicCoap_temperaturaInterna + "'...\n")

        try:
            # Wait until the response is ready
            response_temperaturaInterna = await protocol.request(req_temperaturaInterna).response
        except Exception as e:
            print("[CoAP] Failed to fetch resource for endpoint '" + topicCoap_temperaturaInterna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s, CoAP]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaInterna, response_temperaturaInterna.code, response_temperaturaInterna.payload.decode("utf-8")))


        # Esterna

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaEsterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaEsterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + ", CoAP]  Sending GET request for endpoint '" + topicCoap_temperaturaEsterna + "'...\n")

        try:
            # Wait until the response is ready
            response_temperaturaEsterna = await protocol.request(req_temperaturaEsterna).response
        except Exception as e:
            print("[CoAP] Failed to fetch resource for endpoint '" + topicCoap_temperaturaEsterna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s, CoAP]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaEsterna, response_temperaturaEsterna.code, response_temperaturaEsterna.payload.decode("utf-8")))


        time.sleep(5)

if __name__ == "__main__":
        asyncio.run(main())
