"""
Sample structure for a communication point module.
This module describes the basic uses of SimpleSensor.
To make your own module, this is a good place to start.

This module will receive large_number events and log/count them,
once the threshold is reached as set in config/module.conf, shutdown.
"""

# Standard imports, usually used by all communication modules
from simplesensor.collection_modules.collection_base import moduleConfigLoader as configLoader
from simplesensor.shared import ThreadsafeLogger, Message, ModuleProcess
from threading import Thread
<<<<<<< HEAD:communication_modules/communication_base/communicationModule.py
=======

# Module specific imports
import random
>>>>>>> collection_base:collection_modules/collection_base/collectionModule.py

class CommunicationModule(ModuleProcess)

	# You can keep these parameters the same, all modules receive the same params
	# self - reference to self
	# baseConfig - configuration settings defined in /simplesensor/config/base.conf 
	# 			    (https://github.com/AdobeAtAdobe/SimpleSensor/blob/master/config/base.conf)
	# pInBoundQueue - messages from handler to this module
	# pOutBoundQueue - messages from this module to other modules
	# loggingQueue - logging messages for threadsafe logger

	def __init__(self, baseConfig, pInBoundQueue, pOutBoundQueue, loggingQueue):
        """ 
        Initialize new CollectionModule instance.
        """
        super(CollectionModule, self).__init__()

        # Most collection modules will follow a similar pattern...

        # 1. Set up some variables on the self object
        self.outQueue = pOutBoundQueue
        self.inQueue= pInBoundQueue
        self.loggingQueue = loggingQueue
        self.threadProcessQueue = None
<<<<<<< HEAD:communication_modules/communication_base/communicationModule.py
        self.counter = 0
=======
>>>>>>> collection_base:collection_modules/collection_base/collectionModule.py
        self.alive = False

        # 2. Load the module's configuration file
        # Configs
        self.moduleConfig = configLoader.load(self.loggingQueue, __name__)
        self.config = baseConfig

        # 3. Set some constants to the self object from config parameters (if you want)
        self._bigNumberThreshold = self.moduleConfig['BigNumberThreshold']

        # 4. Create a threadsafe logger object
        self.logger = ThreadsafeLogger(loggingQueue, __name__)

    def run(self):
    	"""
    	Main process method, run when the thread's start() function is called.
    	Starts monitoring inbound messages to this module.

        Usually, any messages going out from communication modules to other
        modules will depend on incoming messages.

        Typically, a communication module would handle outgoing messages to
        connected clients over some protocol, but this is a toy example.
    	"""

<<<<<<< HEAD:communication_modules/communication_base/communicationModule.py
        # Begin monitoring inbound queue
        self.listen()

    def listen(self):
        self.threadProcessQueue = Thread(target=self.processQueue)
        self.threadProcessQueue.setDaemon(True)
        self.threadProcessQueue.start()
        self.alive = True
=======
    	# Monitor inbound queue on own thread
        self.listen()

        # For this example, it randomly generates numbers
        # if the number is large, send a `large_number` event
        # with the number as a parameter in the extendedData
        while self.alive:
        	anum = random.randint(1, 100000)
        	if anum > 95000:
        		extraData = {}
        		extraData['the_number'] = anum
        		self.putMessage(
        			'large_number',
        			extraData
        			)

    def listen(self):
        """
        Start thread to monitor inbound messages, declare module alive.
        """

        self.threadProcessQueue = Thread(target=self.processQueue)
        self.threadProcessQueue.setDaemon(True)
        self.threadProcessQueue.start()
        self.alive()

    def putMessage(self, topic, extendedData=None, recipients=['all'], localOnly=False):
    	"""
    	Create an outgoing event object and
    	put it onto the outgoing queue.
    	Must at least provide message topic,
    	rest of the params are optional.
    	"""

    	msg = CollectionPointEvent(
    		self._id, 
    		self._type, 
    		topic, 
    		extendedData=extendedData, 
    		localOnly=localOnly, 
    		recipients=recipients, 
    		eventTime=datetime.datetime.utcnow()
    		)
    	self.outQueue.put(msg)
>>>>>>> collection_base:collection_modules/collection_base/collectionModule.py

    def processQueue(self):
    	"""
    	Process inbound messages on separate thread.
    	When a message is encountered, trigger an event to handle it.
    	Sleep for some small amount of time to avoid overloading.
    	Also receives a SHUTDOWN message from the main process when 
    	the user presses the esc key.
    	"""

        self.logger.info("Starting to watch collection point inbound message queue")
        while self.alive:
            if (self.inQueue.empty() == False):
                self.logger.info("Queue size is %s" % self.inQueue.qsize())
                try:
                    message = self.inQueue.get(block=False,timeout=1)
                    if message is not None:
                        if (message.topic.upper()=="SHUTDOWN" and 
                            message.sender_id.lower()=='main'):
                                self.logger.info("SHUTDOWN command received on %s" % __name__)
                                self.shutdown()
                        else:
                            self.handleMessage(message)
                except Exception as e:
                    self.logger.error("Error, unable to read queue: %s " %e)
                    self.shutdown()
                self.logger.info("Queue size is %s after" % self.inQueue.qsize())
            else:
                time.sleep(.25)

    def handleMessage(self, message):
    	"""
    	Handle messages from other modules to this one.
    	Switch on the message topic, do something with the data fields.
    	"""

        # Parameter checking, data cleaning goes here
        try:
            assert message.topic is not None
            assert message.extended_data is not None
            assert message.extended_data.the_number is not None
        except:
            self.logger.error('Error, invalid message: %s'%message)

        if message.topic == 'large_number':
            self.logger.info('Module %s encountered a large number: %s'%(message._sender, message._extendedData.the_number))
            self.counter += 1
            if self.counter > self._bigNumberThreshold:
                self.shutdown()

    def shutdown(self):
    	"""
    	Shutdown the communication module.
    	Set alive flag to false so it stops looping.
    	Wait for things to die, then exit.
    	"""

    	self.alive = False
        self.logger.info("Shutting down")
        # Do any extra clean up here
        # for example, joining threads if you spawn more
        time.sleep(1)
        self.exit = True