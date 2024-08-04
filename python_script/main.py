import logging
import asyncio
import time

from pickle import GET
from aiocoap import *



# CoAP #

logging.basicConfig(level=logging.INFO)

# CoAP observe
def observation_callback(response):
    print("callback: %r" % response.payload)

async def main():

    protocol = await Context.create_client_context()

    stop = False
    while(True):

        if stop==False:     # Codice eseguito una sola volta

            #req = Message(code=GET, uri='coap://192.168.24.4:5683/temperatura_interna')
            req = Message(code=GET, uri='coap://192.168.104.4:5683/temperatura_interna')

            # OBSERVE
            req.opt.observe = 0     # Set observe bit from None to 0

            try:
                #response = await protocol.request(req).response

                # OBSERVE
                # The message payload is printed whenever a new notification message is received from the server
                protocol_request = protocol.request(req)
                protocol_request.observation.register_callback(observation_callback)
                response = await protocol_request.response
            except Exception as e:
                print('Failed to fetch resource:')
                print(e)
            else:
                # “2.05 Content” is a successful message (is the rough equivalent of HTTP’s “200 OK”)
                print('Result: %s\n%r' % (response.code, response.payload.decode("utf-8")))

            #time.sleep(7)

        stop = True

if __name__ == "__main__":
    asyncio.run(main())
