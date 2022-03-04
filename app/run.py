#!/usr/bin/env python3
import json
import os
import traceback
import asyncio
from aioairctrl import CoAPClient # "aioairctrl @ git+https://github.com/betaboon/aioairctrl@v0.2.1"
import datetime
from mqttPublishThread import mqttPublishThread
import queue
BUF_SIZE = 100
q = queue.Queue(BUF_SIZE)

import logging
logger = logging.getLogger(__name__)

#global state of airfilter
state={}
#####
# Values that will be read from coapconfig.json
#####
# global lookup mapping for coapKeys <=> mqttKeys and further settings
#publishParamsList = [
#                     {'coapKey':'ConnectType', 'mqttKey':'status'},
#                     {'coapKey':'pm25', 'mqttKey':'sensor/pm25/state', 'updateOnlyIfDifferenceIsMoreThen':1},
#                     {'coapKey':'tvoc', 'mqttKey':'sensor/tvoc/state'},
#                     {'coapKey':'iaql', 'mqttKey':'sensor/allergene/state'},
#                     {'coapKey':'aqil', 'mqttKey':'sensor/brightness/state'},
#                     {'coapKey':'fltsts0', 'mqttKey':'filter/prefilterclean'},
#                     {'coapKey':'fltsts1', 'mqttKey':'filter/hepafilterreplace'},
#                     {'coapKey':'fltsts2', 'mqttKey':'filter/activecarbonfilterreplace'},
#                     {'coapKey':'mode', 'mqttKey':'mode', 'mqttControll':True},
#                     {'coapKey':'om', 'mqttKey':'fanspeed'},
#                     {'coapKey':'pwr', 'mqttKey':'power'},
#                     {'coapKey':'uil', 'mqttKey':'buttonlight'}
#                    ]
publishParamsList = []
# mqtt prefix of sensor
mqttSensorPrefix = "philips"
# coapHost
coapHost = "10.0.0.1"

async def set_control_value_from_mqtt(client, topic, msg):
	logger.info(f"ASYNC {topic} - {msg} ")
	#remove mqttSensorPrefix from Topic
	topic = topic[len(mqttSensorPrefix+'/'):]
	try:
		if topic in state:
			if state[topic] != msg:
				coapKeyList = [d["coapKey"] for d in publishParamsList if d['mqttKey'] == topic]
				logger.info(f"coaKeyList {coapKeyList}")
				coapKey = coapKeyList[0]
				data = {coapKey: msg}
				logger.info(f"set_control_values(data={data})")
				await client.set_control_values(data=data)
			else:
				logger.info("recived already set state")
		else:
			logger.info(f"Don't have any state for {topic} yet")
	except Exception as e:
		logger.error("Error while processing message")
		logger.error(str(e))

def msgCallback(topic, msg, params): 
	"""Callback function on mqtt messages

		Function handoff tasks to the asyncio Loop
	"""
	logger.info(f"Callback {msg} - {params}")
	asyncio.run_coroutine_threadsafe(set_control_value_from_mqtt(params['client'], topic, msg), params['loop'])#, event_loop)
	
async def main():
	global state    # Needed to modify global copy of globvar
	#prepare upload consumer
	pT = mqttPublishThread(q, name='mqttPublishThread')
	pT.start()
	logger.info(f"Start COAP - {coapHost}")
	client = await CoAPClient.create(host=coapHost)
	logger.info("First GETTING STATUS")

	#Subscribe to all mqtt topics 
	#where in publishParamsList mqttControll is True
	logger.info("Subs")
	subList = [d for d in publishParamsList if 'mqttControll' in d and d['mqttControll'] == True ]
	for sub in subList:
		logger.debug(f"Subscription {sub['mqttKey']}")
		pT.subscribe(mqttSensorPrefix+'/'+sub['mqttKey'],msgCallback,params={'loop': asyncio.get_event_loop(), 'client':client})

	
	try:
		logger.info("observe")
		canceled = False
		timeout_count = 0
		while not canceled:
			try:
				logger.info("start observe")
				async for res in client.observe_status(inital_timeout=180 + (timeout_count*60)):
					timeout_count = 0
					#for res in status:
					now = datetime.datetime.now()
					logger.info(f"Got State {now}")
					logger.debug(res)

					for d in publishParamsList:
					    value = res[d['coapKey']]
					    #check values
					    if state.get(d['mqttKey']) is None or state.get(d['mqttKey']) != value:
					        if type(value) == int and state.get(d['mqttKey']) is not None and \
					        	'updateOnlyIfDifferenceIsMoreThen' in d and type(d['updateOnlyIfDifferenceIsMoreThen']) == int and \
					        	(state.get(d['mqttKey']) - d['updateOnlyIfDifferenceIsMoreThen']) <= value <= (state.get(d['mqttKey'])+ d['updateOnlyIfDifferenceIsMoreThen']):
					        		#ignore if +-1
					        		logger.info(f"Value in updateOnlyIfDifferenceIsMoreThen {d['mqttKey']}")
					        		continue

					        logger.info(f"Publish {mqttSensorPrefix}/{d['mqttKey']} => {value}")
					        q.put({'topic': mqttSensorPrefix+'/'+d['mqttKey'], 'payload':value })
					        state[d['mqttKey']] = value
					#await asyncio.sleep(10)
				logger.info("Restarting observe")
				if timeout_count <= 10:
					timeout_count += 1
				else:
					logger.warning(f"Timeout excess {timeout_count}")
					
			except asyncio.CancelledError as e:
				logger.info("Async io cancelled")
	except (KeyboardInterrupt):
		logger.info("Keyboard interrupt")
	except Exception as e:
		logger.error("Exception")
		logger.error(traceback.format_exc())
		logger.error(e)
	finally:
		logger.info("Shutting down")
		if client:
			logger.info("Waiting for client")
			await client.shutdown()
		logger.info("Waiting for mqtt thread")
		pT.join() # wait for thread (infinity)


if __name__ == "__main__":
	#global publishParamsList, mqttSensorPrefix, coapHost
	#reading settings
	settingsFile = 'settings/coapconfig.json'
	with open(settingsFile) as f:
		config = json.load(f)
		#set config values to global vars
		if 'publishParamsList' in config:
			publishParamsList = config['publishParamsList']
		else:
			logger.error(f"{settingsFile} is missing a 'publishParamsList'")
			os.exit(1)

		if 'mqttSensorPrefix' in config:
			mqttSensorPrefix = config['mqttSensorPrefix']
		else:
			logger.error(f"{settingsFile} is missing a 'mqttSensorPrefix'")
			os.exit(1)

		if 'coapHost' in config:
			coapHost = config['coapHost']
		else:
			logger.error(f"{settingsFile} is missing a 'coapHost'")
			os.exit(1)

		f.close()
	asyncio.run(main())