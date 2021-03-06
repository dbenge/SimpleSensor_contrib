"""
MQTT client module
"""

import logging
import time
import json
from threading import Thread
import paho.mqtt.client as mqtt
from simplesensor.shared import ThreadsafeLogger, ModuleProcess, Message
from . import moduleConfigLoader as configLoader

class MQTTClientModule(ModuleProcess):
    """ Threaded MQTT client for processing and publishing outbound messages"""

    def __init__(self, baseConfig, pInBoundEventQueue, pOutBoundEventQueue, loggingQueue):

        super(MQTTClientModule, self).__init__()
        self.config = baseConfig
        self.alive = True
        self.inQueue = pInBoundEventQueue

        # Module config
        self.moduleConfig = configLoader.load(self.loggingQueue, __name__)

        # Constants
        self._keepAlive = self.moduleConfig['MqttKeepAlive']
        self._feedName = self.moduleConfig['MqttFeedName']
        self._username = self.moduleConfig['MqttUsername']
        self._key = self.moduleConfig['MqttKey']
        self._host = self.moduleConfig['MqttHost']
        self._port = self.moduleConfig['MqttPort']
        self._publishJson = self.moduleConfig['MqttPublishJson']

        # MQTT setup
        self._client = mqtt.Client()
        self._client.username_pw_set(self._username, self._key)
        self._client.on_connect    = self.onConnect
        self._client.on_disconnect = self.onDisconnect
        self._client.on_message    = self.onMessage
        self.mqttConnected = False

        # Logging setup
        self.logger = ThreadsafeLogger(loggingQueue, "MQTT")

    def onConnect(self, client, userdata, flags, rc):
        self.logger.debug('MQTT onConnect called')
        # Result code 0 is success
        if rc == 0:
            self.mqttConnected = True

            # Subscribe to feed here
        else:
            self.logger.error('MQTT failed to connect: %s'%rc)
            raise RuntimeError('MQTT failed to connect: %s'%rc)

    def onDisconnect(self, client, userdata, rc):
        self.logger.debug('MQTT onDisconnect called')
        self.mqttConnected = False
        if rc != 0:
            self.logger.debug('MQTT disconnected unexpectedly: %s'%rc)
            self.handleReconnect(rc)

    def onMessage(self, client, userdata, msg):
        self.logger.debug('MQTT onMessage called for client: %s'%client)

    def connect(self):
        """ Connect to MQTT broker
        Skip calling connect if already connected.
        """
        if self.mqttConnected:
            return

        self._client.connect(self._host, port=self._port, keepalive=self._keepAlive)

    def disconnect(self):
        """ Check if connected"""
        if self.mqttConnected:
            self._client.disconnect()

    def subscribe(self, feed=False):
        """Subscribe to feed, defaults to feed specified in config"""
        if not feed: feed = self._feedName
        self._client.subscribe('{0}/feeds/{1}'.format(self._username, feed))

    def publish(self, value, feed=False):
        """Publish a value to a feed"""
        if not feed: feed = self._feedName
        self._client.publish('{0}/feeds/{1}'.format(self._username, feed), payload=value)

    def flattenDict(self, aDict):
        """ Get average of simple dictionary of numerical values """
        try:
            val = float(sum(aDict[key] for key in aDict)) / len(aDict)
        except Exception as e:
            self.logger.error('Error flattening dict, returning 0: %s'%e)
            return 0
        return val

    def publishJsonMessage(self, message):
        msg_str = self.stringifyMessage(message)
        self.publish(msg_str)

    def stringifyMessage(self, message):
        """ Dump into JSON string """
        return json.dumps(message.__dict__).encode('utf8')

    def processQueue(self):
        """ Process incoming messages. """

        while self.alive:
            # Pump the loop
            self._client.loop(timeout=1)
            if (self.inQueue.empty() == False):
                try:
                    message = self.inQueue.get(block=False,timeout=1)
                    if message is not None and self.mqttConnected:
                        if (message.topic.upper()=="SHUTDOWN" and
                            message.sender_id.lower()=='main'):
                            self.logger.debug("SHUTDOWN command handled")
                            self.shutdown()
                        else:
                            # Send message as string or split into channels
                            if self._publishJson:
                                self.publishJsonMessage(message)
                            else:
                                self.publishValues(message)

                except Exception as e:
                    self.logger.error("MQTT unable to read queue : %s " %e)
            else:
                time.sleep(.25)

    def shutdown(self):
        self.logger.info("Shutting down")
        self.alive = False
        time.sleep(1)
        self.exit = True

    def run(self):
        """ Thread start method"""
        self.logger.info("Running MQTT")

        self.connect()
        self.alive = True

        # Start queue loop
        self.processQueue()