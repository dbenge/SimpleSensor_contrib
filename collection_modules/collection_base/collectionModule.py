"""
Sample structure for a collection point module.
This module describes the basic uses of SimpleSensor.
To make your own module, this is a good place to start.
"""

# Standard imports, usually used by all collection modules
from simplesensor.collection_modules.collection_base import moduleConfigLoader as configLoader
from simplesensor.shared.collectionPointEvent import CollectionPointEvent
from simplesensor.shared.threadsafeLogger import ThreadsafeLogger
from multiprocessing import Process
from threading import Thread

# Module specific imports
import random

class CollectionModule(Process)

	# You can keep these parameters the same, all modules receive the same params
	# self - reference to self
	# baseConfig - configuration settings defined in /simplesensor/config/base.conf 
	# 				(https://github.com/AdobeAtAdobe/SimpleSensor/blob/master/config/base.conf)
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
                        if message == "SHUTDOWN":
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

    	# neither of these are needed, just to illustrate how inbound messages could be used
    	# in many cases, collection_modules will only collect data and send out events
    	# with no regard for what other modules are emitting
        if message._topic == 'hello':
            self.logger.info('Module %s says "%s"'%(message._sender, message._topic))
        elif message._topic == 'goodbye':
        	self.logger.info('Module %s told me to shutdown'%message._sender)
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