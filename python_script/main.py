import logging
import asyncio
import time
import datetime

from pickle import GET
from aiocoap import *                   # CoAP

import paho.mqtt.publish as publish     # MQTT



# CoAP #

logging.basicConfig(level=logging.INFO)

async def main():

    ip_coap_server = "192.168.195.4"    # Indirizzo IP dell'ESP

    topicCoap_temperaturaInterna = "temperatura_interna"
    topicCoap_temperaturaEsterna = "temperatura_esterna"


    protocol = await Context.create_client_context()

    while True:

        publish.single("sampling_rate", 3000, hostname="localhost")     # localhost: Indirizzo IP del mio pc con mosquitto



        # Chiedo i valori delle temperature al server ESP #


        # Interna

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaInterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaInterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Sending GET request for endpoint '" + topicCoap_temperaturaInterna + "'...\n")

        try:
            # Wait until the response is ready
            response_temperaturaInterna = await protocol.request(req_temperaturaInterna).response
        except Exception as e:
            print("Failed to fetch resource for endpoint '" + topicCoap_temperaturaInterna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaInterna, response_temperaturaInterna.code, response_temperaturaInterna.payload.decode("utf-8")))


        # Esterna

        # mtype=NON:  request/response using non confirmable messages
        req_temperaturaEsterna = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topicCoap_temperaturaEsterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Sending GET request for endpoint '" + topicCoap_temperaturaEsterna + "'...\n")

        try:
            # Wait until the response is ready
            response_temperaturaEsterna = await protocol.request(req_temperaturaEsterna).response
        except Exception as e:
            print("Failed to fetch resource for endpoint '" + topicCoap_temperaturaEsterna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topicCoap_temperaturaEsterna, response_temperaturaEsterna.code, response_temperaturaEsterna.payload.decode("utf-8")))


        time.sleep(2)

if __name__ == "__main__":
        asyncio.run(main())
