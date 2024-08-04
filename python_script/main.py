import logging
import asyncio
import time

from pickle import GET
from aiocoap import *



# CoAP #

logging.basicConfig(level=logging.INFO)

async def main():

    protocol = await Context.create_client_context()

    while(True):

        #req = Message(code=GET, uri='coap://130.136.2.70:5683/temperatura_interna')
        req = Message(code=GET, uri='coap://192.168.24.4:5683/temperatura_interna')

        try:
            response = await protocol.request(req).response
        except Exception as e:
            print('Failed to fetch resource:')
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print('Result: %s\n%r' % (response.code, response.payload.decode("utf-8")))

        time.sleep(7)

if __name__ == "__main__":
        asyncio.run(main())
