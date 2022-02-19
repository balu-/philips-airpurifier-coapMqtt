# philips-airpurifier-coapMqtt
Some code to make philips air purifier accessible and controllable via mqtt

I wrote this code for me to have the air quality values of my philips airpurifier handy, 
and beeing able to log them. Further more I wanted to controll the airpurifier via mqtt to be able to integrate it into my smart home setup.

This scripts / This docker-container creates a bridge between coap (the protocol used by the purifier) and mqtt. It is push based and doesn't poll values, so propagation should be near instantanious.

## How to run

Setup your Airpurifier to use your wifi and find its IP-Adress.
After that adapt the settings in `coapconfig.json` and `mqttconfig.json`,
build the docker-container, and run it (either using docker-compse, or docker. If you use docker you need to mount the settings folder to `/app/settings`).

## Settings

The settings are stored in the `settings` folder.
There should be to files:

### mqttconfig.json
This file is used to store all settings needed to connect to the mqtt broker.
Values should be selfexplainatory.
_Important_: `mqttPrefix` should end with a '/'
#### Sample
```
{
    "mqttAddress": "192.168.100.1",
    "mqttPort": 1883,
    "username": "coapMqttUser",
    "password": "coapMqttPassword",
    "mqttPrefix": "coap2mqtt/"
}
```

### coapconfig.json
This is the main config file, it sets the ip of the airpurifier (`coapHost`) and the prefix used in mqtt to publish the values (`mqttSensorPrefix`). Further more the mapping of coapKeys to mqttKeys is defined here (`publishParamsList`) but there shouldn't be any need to change those mappings.

#### Sample
```
{
    "publishParamsList": [
                     {"coapKey":"ConnectType", "mqttKey":"status"},
                     {"coapKey":"pm25", "mqttKey":"sensor/pm25/state", "updateOnlyIfDifferenceIsMoreThen":1},
                     {"coapKey":"tvoc", "mqttKey":"sensor/tvoc/state"},
                     {"coapKey":"iaql", "mqttKey":"sensor/allergene/state"},
                     {"coapKey":"aqil", "mqttKey":"sensor/brightness/state"},
                     {"coapKey":"fltsts0", "mqttKey":"filter/prefilterclean"},
                     {"coapKey":"fltsts1", "mqttKey":"filter/hepafilterreplace"},
                     {"coapKey":"fltsts2", "mqttKey":"filter/activecarbonfilterreplace"},
                     {"coapKey":"mode", "mqttKey":"mode", "mqttControll": true},
                     {"coapKey":"om", "mqttKey":"fanspeed", "mqttControll": true},
                     {"coapKey":"pwr", "mqttKey":"power", "mqttControll": true},
                     {"coapKey":"uil", "mqttKey":"buttonlight"}
                    ],
    "mqttSensorPrefix": "philips-airpurifier",
    "coapHost": "10.0.0.1"
}
```

### Exposed Mqtt structure

- philips-airpurifier
	- sensor
		- pm25
			- state = <value | number>
		- tvoc
			- state = <value | number>
		- allergene
		    - state = <value | number>
		- brightness
			- state = <value | number>
	- status = <value | string Online>
	- filter
		- prefilterclean = <value | hours>
		- hepafilterreplace = <value | hours>
		- activecarbonfilterreplace = <value | hours>
	- mode = <value | AG | S | T ...>
	- fanspeed = <value | s | 1 | 2 | 3 ...>
	- power = <value | 1 | 0 >
	- buttonlight = <value>



### Tested Devices
 - Philips AC3033
#### Should probably also work with
 - AC1214
 - AC2729
 - AC2889
 - AC2939
 - AC3059
 - AC3829
 - AC3858
 - AC4236
