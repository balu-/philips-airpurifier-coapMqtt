# philips-airpurifier-coapMqtt
Some code to make philips air purifier accessible and controllable via mqtt

I wrote this code for me to have the air quality values of my philips airpurifier handy, 
and beeing able to log them. Further more I wanted to controll the airpurifier via mqtt to be able to integrate it into my smart home setup.

This scripts / This docker-container creates a bridge between coap (the protocol used by the purifier) and mqtt. It is push based and doesn't poll values, so propagation should be near instantanious.

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
