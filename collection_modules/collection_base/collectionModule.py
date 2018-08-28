"""
Sample structure for a collection point module.
This module describes the basic uses of SimpleSensor.
To make your own module, this is a good place to start.
"""

# Standard imports, usually used by all collection modules
from simplesensor.collection_modules.collection_base import moduleConfigLoader as configLoader
from simplesensor.shared import Message, ThreadsafeLogger, ModuleProcess
from multiprocessing import Process
from threading import Thread

# Module specific imports
import random

class CollectionModule(ModuleProcess)

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
        # Queues
        self.outQueue = pOutBoundQueue
        self.inQueue= pInBoundQueue
        self.loggingQueue = loggingQueue
        self.threadProcessQueue = None
        self.alive = False

        # 2. Load the module's configuration file
        # Configs
        self.moduleConfig = configLoader.load(self.loggingQueue, __name__)
        self.config = baseConfig

        # 3. Set some constants to the self object from config parameters (if you want)
        self._id = moduleConfig['CollectionPointId']
        self._type = moduleConfig['CollectionPointType']

        # 4. Create a threadsafe logger object
        self.logger = ThreadsafeLogger(loggingQueue, __name__)

    def run(self):
    	"""
    	Main process method, run when the thread's start() function is called.
    	Starts monitoring inbound messages to this module, and collection logic goes here.
    	For example, you could put a loop with a small delay to keep polling the sensor, etc.
    	When something is detected that's relevant, put a message on the outbound queue.
    	"""

    	# Monitor inbound queue on own thread
        self.listen()

        # For this example, it randomly generates numbers
        # if the number is large, send a `large_number` event
        # with the number as a parameter in the extendedData
        while self.alive:
        	anum = random.randint(1, 100000)
        	if anum > 95000:
        		extendedData = {}
        		extendedData['the_number'] = anum
        		msg = self.buildMessage(
        			topic='large_number',
        			extendedData=extendedData)
                self.putMessage(msg)

    def listen(self):
        """
        Start thread to monitor inbound messages, declare module alive.
        """

        self.threadProcessQueue = Thread(target=self.processQueue)
        self.threadProcessQueue.setDaemon(True)
        self.threadProcessQueue.start()
        self.alive()

    def buildMessage(self, topic, extendedData={}, recipients=['communication_modules']):
    	"""
    	Create a Message instance.

    	topic (required): message type
        sender_id (required): id property of original sender
        sender_type (optional): type of sender, ie. collection point type, module name, hostname, etc
        extended_data (optional): payload to deliver to recipient(s)
        recipients (optional): module name, which module(s) the message will be delivered to, ie. `websocket_server`.
                                use an array of strings to define multiple modules to send to.
                                use 'all' to send to all available modules.
                                use 'local_only' to send only to modules with `low_cost` prop set to True.
                                [DEFAULT] use 'communication_modules' to send only to communication modules.
                                use 'collection_modules' to send only to collection modules.
    	"""

    	msg = Message(
            topic=topic,
            sender_id=self._id, 
            sender_type=self._type, 
            extended_data=extendedData, 
            recipients=recipients, 
            timestamp=datetime.datetime.utcnow())
    	return msg

    def putMessage(self, msg):
        """
        Put message onto outgoing queue.
        """
        self.outQueue.put(msg)

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

    	# neither of these are needed, just to illustrate how inbound messages could be used
    	# in many cases, collection_modules will only collect data and send out events
    	# with no regard for what other modules are emitting
        if message.topic == 'hello':
            self.logger.info('Module %s says "%s"'%(message._sender, message._topic))
        elif message.topic == 'goodbye':
        	self.logger.info('Module %s told me to shutdown'%message._sender)
            self.shutdown()
        elif message.topic == 'SHUTDOWN' and message.sender_id == 'main':
            self.logger.warn("SHUTDOWN command from main handled.")
            self.shutdown()

    def shutdown(self):
    	"""
    	Shutdown the collection module.
    	Set alive flag to false so it stops looping.
    	Wait for things to die, then exit.
    	"""

    	self.alive = False
        self.logger.info("Shutting down")
        # Do any extra clean up here
        # for example, joining threads if you spawn more
        time.sleep(1)
        self.exit = True