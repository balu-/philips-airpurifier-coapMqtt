# post to db
import paho.mqtt.client as mqtt
import threading
import logging
import time
import json
import logging
from collections.abc import Callable
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
                    format='(%(threadName)-9s) %(message)s',)

class mqttPublishThread(threading.Thread):
    #def __init__(self, group=None, target=None, name=None,
    #             args=(), kwargs=None, verbose=None):
    def __init__(self, queue, name=None):
        super(mqttPublishThread,self).__init__(daemon=True)
        self.target = None #target
        self.name = name
        self.queue = queue
        self._subscribers = {}
        with open("settings/mqttconfig.json") as file:
            self.__config = json.load(file) #mqttRouterConfig("mqttconfig.json")
            self.__client = mqtt.Client()
            self.__client.username_pw_set(self.__config["username"], self.__config["password"])
            self.__client.on_message = self._on_message
            self.__client.on_connect = self._on_connect
            self.__client.on_disconnect = self._on_disconnect
             #init connection state
            self.__client.connected_flag = threading.Event()
            self.__client.connected_flag.clear()  #set to false
            try:
                self.__client.connect(self.__config["mqttAddress"], self.__config["mqttPort"], keepalive=60)
                self.__client.loop_start()
            except ConnectionRefusedError as e:
                logger.error("Could not connect to mqtt")
                raise e
            #self.__client.loop_forever()
            logger.info("mqttloop started")
        return

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.__client.connected_flag.set()  #set to true
            logger.info("connected OK Returned code=" + str(rc))
            #subscribe to all subscriber topics:
            for key, value in self._subscribers.items():
                logger.info("subscribe :" + self.__config['mqttPrefix']+key)
                self.__client.subscribe(self.__config['mqttPrefix']+key)
        else:
            logger.info("Bad connection Returned code=", rc)

    def _on_disconnect(self, client, userdata, rc):
        logger.info("disconnecting reason  " + str(rc))
        if rc != 0:
            print("Unexpected disconnection.")
        self.__client.connected_flag.clear()  #set to false

    def _on_message(self, client, userdata, msg):
        logger.info(msg.topic + " " + str(msg.payload))
        #topic_matches_sub(sub, topic) can be used to check whether a topic matches a subscription.
        for key, value in self._subscribers.items():
            logger.debug(f"Check for match {self.__config['mqttPrefix']+key} -> {msg.topic}")
            if mqtt.topic_matches_sub(self.__config['mqttPrefix']+key, msg.topic):
                for callback_value in value:
                    #call callback
                    #func(topic,msg,params)
                    try:
                        msg_str = ""
                        try:
                            msg_str = str(msg.payload.decode("utf-8"))
                        except Exception as e:
                            logger.warn(e)
                            msg_str = str(msg.payload)
                        
                        logger.debug(f"payload {msg_str} - value {callback_value}")
                        if callback_value['params'] is not None:
                            callback_value['callback'](key,msg_str,callback_value['params'])#todo fix
                        else:
                            callback_value['callback'](key,msg_str)#todo fix
                    except Exception as e:
                        logger.error(e) 

    def subscribe(self,topic :str, callbackfunction: Callable[[str, str, ...], None], params=None) -> None: 
        """Subscribs to a mqtt topic and calls the callback funktion on messages

        if the "params" parameter isn't passed, its not added on calling the "callbackfunction"

        Parameters
        ----------
        topic : str
            the topic which should be subscribed to

        callbackfunction : function(topic, msg, (optional) params)
        pass the function that will be called on message in 'topic'.
        The 'callbackfunction' should accept 2 or 3 parameters which are:
            topic :str - the topic of the recived message
            msg :str - the message recived in topic
            (optional) params : the params value you passed when calling this subscribe function

        params: 
        some value that you need in your callback function

        """ 
        logger.info(f"Subscribe request to {topic} ")
        if topic in self._subscribers:
            self._subscribers[topic].append({'callback': callbackfunction, 'params':params})
        else:
            self._subscribers[topic] = [{'callback': callbackfunction, 'params':params}]
            logger.info("fresh subscribe :" + self.__config['mqttPrefix']+topic)
            self.__client.subscribe(self.__config['mqttPrefix']+topic) #subscribe

    def run(self):
        while True:
            #if not q.empty():
            item = self.queue.get()
            logging.debug('Getting ' + str(item)
                              + ' : ' + str(self.queue.qsize()) + ' items in queue')
            self.__client.publish(self.__config['mqttPrefix']+item['topic'], payload=item['payload']) #(topic, payload=None, qos=0, retain=False)
            
        return
