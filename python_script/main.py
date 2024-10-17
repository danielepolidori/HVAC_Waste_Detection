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

        #req = Message(code=GET, uri='coap://192.168.119.4:5683/temperatura_interna')
        #req = Message(code=GET, uri='coap://192.168.191.4/temperatura_interna')
        req = Message(code=GET, uri='coap://192.168.191.4/temperatura_esterna')

        try:
            response = await protocol.request(req).response
        except Exception as e:
            print('Failed to fetch resource:')
            print(e)
        else:
            # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
            print('Result: %s\n%r\n' % (response.code, response.payload.decode("utf-8")))

        time.sleep(2)   # numero temperature ricevute: 9, [68] -- [2, 5, 3 (10 GET), 1 (3), 4 (9), 2 (8)]          # [hotspot vicino]
        #time.sleep(5)      # 5, 14, [24, 19] --
        #time.sleep(8)      # -- [1 (4)]

if __name__ == "__main__":
        asyncio.run(main())
