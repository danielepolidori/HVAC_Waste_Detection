import logging
import asyncio
import time
import datetime

from pickle import GET
from aiocoap import *



# CoAP #

logging.basicConfig(level=logging.INFO)

async def main():

    ip_coap_server = "192.168.154.4"    # IP dell'ESP

    topic_coap_temperatura_interna = "temperatura_interna"
    topic_coap_temperatura_esterna = "temperatura_esterna"


    protocol = await Context.create_client_context()

    while True:

        # Chiedo i valori delle temperature al server ESP #


        # Interna

        # mtype=NON:  request/response using non confirmable messages
        req = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topic_coap_temperatura_interna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Sending GET request for endpoint '" + topic_coap_temperatura_interna + "'...\n")

        try:
            # wait until the response is ready
            response = await protocol.request(req).response
        except Exception as e:
            print("Failed to fetch resource for endpoint '" + topic_coap_temperatura_interna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topic_coap_temperatura_interna, response.code, response.payload.decode("utf-8")))


        # Esterna

        # mtype=NON:  request/response using non confirmable messages
        req = Message(mtype=NON, code=GET, uri="coap://" + ip_coap_server + "/" + topic_coap_temperatura_esterna)

        print("[" + datetime.datetime.now().strftime('%H:%M:%S') + "]  Sending GET request for endpoint '" + topic_coap_temperatura_esterna + "'...\n")

        try:
            # wait until the response is ready
            response = await protocol.request(req).response
        except Exception as e:
            print("Failed to fetch resource for endpoint '" + topic_coap_temperatura_esterna + "':")
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print("[%s]  RESULT for endpoint '%s':\n(%s)  %r\n" % (datetime.datetime.now().strftime('%H:%M:%S'), topic_coap_temperatura_esterna, response.code, response.payload.decode("utf-8")))


        time.sleep(2)

if __name__ == "__main__":
        asyncio.run(main())
