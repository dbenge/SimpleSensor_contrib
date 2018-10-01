"""
Sample structure for a collection point module.
This module describes the basic uses of SimpleSensor.
To make your own module, this is a good place to start.
"""

from simplesensor.collection_modules.nfc_bcard_reader import moduleConfigLoader as configLoader
from simplesensor.shared import Message, ThreadsafeLogger, ModuleProcess
from multiprocessing import Process
from threading import Thread
import time 
import json
import struct
import datetime
from smartcard.scard import *
import smartcard.util

_HEADER_SIZE = 6

class CollectionModule(ModuleProcess):

    # You can keep these parameters the same, all modules receive the same params
    # self - reference to self
    # baseConfig - configuration settings defined in /simplesensor/config/base.conf 
    #               (https://github.com/AdobeAtAdobe/SimpleSensor/blob/master/config/base.conf)
    # pInBoundQueue - messages from handler to this module
    # pOutBoundQueue - messages from this module to other modules
    # loggingQueue - logging messages for threadsafe logger

    def __init__(self, baseConfig, pInBoundQueue, pOutBoundQueue, loggingQueue):
        """ 
        Initialize new CollectionModule instance.
        """
        super(CollectionModule, self).__init__(baseConfig, pInBoundQueue, pOutBoundQueue, loggingQueue)

        # Most collection modules will follow a similar pattern...

        # 1. Set up some variables on the self object
        # Queues
        self.outQueue = pOutBoundQueue
        self.inQueue= pInBoundQueue
        self.loggingQueue = loggingQueue
        self.threadProcessQueue = None
        self.alive = False

        self.context = None
        self.reader = None

        # 2. Load the module's configuration file
        # Configs
        self.moduleConfig = configLoader.load(self.loggingQueue, __name__)
        self.config = baseConfig

        # 3. Set some constants to the self object from config parameters (if you want)
        self._id = self.moduleConfig['CollectionPointId']
        self._type = self.moduleConfig['CollectionPointType']
        self._port = self.moduleConfig['ReaderPortNumber']

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
        self.alive = True

        while self.context == None:
            self.establish_context()

        while self.alive:
            while self.reader == None:
                self.reader = self.get_reader()
                if self.reader is None:
                    self.logger.info('Waiting for 5 seconds before '
                    + 'trying to find readers again. Is it plugged in?')
                    time.sleep(5)

            # connect to card
            card = self.get_card()
            if card is None: 
                continue

            # get block #10 and 11 of card,
            # contains the attendee ID
            msg = [0xFF, 0xB0, 0x00, bytes([10])[0], 0x04]
            chunk_one = self.send_transmission(card, msg)
            if chunk_one is None:
                self.reader = None
                continue
            msg = [0xFF, 0xB0, 0x00, bytes([11])[0], 0x04]
            chunk_two = self.send_transmission(card, msg)
            if chunk_two is None:
                self.reader = None
                continue

            # the id is in B1-3 of block 10
            # and B0-2 of block 11
            attendee_id_bytes = bytearray(chunk_one[1:4]+chunk_two[0:3])
            attendee_id = attendee_id_bytes.decode('UTF-8')
            xdata = {
                'attendee_id': attendee_id
            }
            msg = self.build_message(topic='scan_in', extendedData=xdata)
            self.logger.info('Sending message: {}'.format(msg))
            self.put_message(msg)

            self.reader = None

            # sleep for a bit to avoid double scanning
            time.sleep(5)

    def establish_context(self):
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        if hresult != SCARD_S_SUCCESS:
            self.logger.error(
                'Unable to establish context: {}'.format(
                    SCardGetErrorMessage(hresult)))
            return
        self.context = hcontext

    def get_reader(self):
        hresult, readers = SCardListReaders(self.context, [])
        if hresult != SCARD_S_SUCCESS:
            self.logger.error(
                'Failed to list readers: {}'.format(
                    SCardGetErrorMessage(hresult)))
            return
        if len(readers)<1 or len(readers)-1<self._port:
            self.logger.error(
                'Not enough readers attached. {} needed, {} attached'.format(
                    (self._port+1), (len(readers))))
            return
        else:
            return readers[self._port]

    def get_card(self, mode=None, protocol=None):
        hresult, hcard, dwActiveProtocol = SCardConnect(
                self.context,
                self.reader,
                mode or SCARD_SHARE_SHARED, 
                protocol or (SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1))
        if hresult != SCARD_S_SUCCESS:
            return
        else:
            return hcard

    def send_transmission(self, card, msg, protocol=None):
        hresult, response = SCardTransmit(
                            card, 
                            protocol or SCARD_PCI_T1, 
                            msg)
        if hresult != SCARD_S_SUCCESS:
            self.logger.error(
                'Failed to send transmission: {}'.format(
                    SCardGetErrorMessage(hresult)))
            return
        else:
            return response[:-2]

    def listen(self):
        """
        Start thread to monitor inbound messages, declare module alive.
        """
        self.threadProcessQueue = Thread(target=self.process_queue)
        self.threadProcessQueue.setDaemon(True)
        self.threadProcessQueue.start()

    def build_message(self, topic, extendedData={}, recipients=['communication_modules']):
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

    def put_message(self, msg):
        """
        Put message onto outgoing queue.
        """
        self.outQueue.put(msg)

    def process_queue(self):
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
                        self.handle_message(message)
                except Exception as e:
                    self.logger.error("Error, unable to read queue: %s " %e)
                    self.shutdown()
                self.logger.info("Queue size is %s after" % self.inQueue.qsize())
            else:
                time.sleep(.25)

    def handle_message(self, message):
        """
        Handle messages from other modules to this one.
        Switch on the message topic, do something with the data fields.
        """
        if message.topic.upper()=='SHUTDOWN' and message.sender_id=='main':
            self.shutdown()

    def shutdown(self):
        """
        Shutdown the collection module.
        Set alive flag to false so it stops looping.
        Wait for things to die, then exit.
        """

        self.alive = False
        print("Shutting down nfc_bcard_reader")
        time.sleep(1)
        self.exit = True