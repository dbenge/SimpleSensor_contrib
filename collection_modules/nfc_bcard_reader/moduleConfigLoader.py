'''
Module specific config loader
Any changes you make to module.conf should be reflected here
Optionally add a secrets.conf in the same directory to stick in some secret keys.
''' 

from simplesensor.shared.threadsafeLogger import ThreadsafeLogger
import configparser
import os.path

def load(loggingQueue, name):
	""" Load module specific config into dictionary, return it"""    
	logger = ThreadsafeLogger(loggingQueue, '{0}-{1}'.format(name, 'ConfigLoader'))
	thisConfig = {}
	configParser = configparser.ConfigParser()

	thisConfig = loadSecrets(thisConfig, logger, configParser)
	thisConfig = loadModule(thisConfig, logger, configParser)
	return thisConfig

def loadSecrets(thisConfig, logger, configParser):
	""" Load module specific secrets """
	try:
		with open(os.path.join(os.path.dirname(__file__), 'config', 'secrets.conf')) as f:
			configParser.readfp(f)
			configFilePath = "/secrets.conf"
	except IOError:
		configParser.read(os.path.join(os.path.dirname(__file__),"./config/secrets.conf"))
		configFilePath = os.path.join(os.path.dirname(__file__),"./config/secrets.conf")
		exit

	thisConfig['Secrets'] = {}

	""" Example secret key """
	# try:
	#     configValue=configParser.get('Secrets','secret_key')
	# except:
	#     configValue = ""
	# logger.info("Secret key : %s" % configValue)
	# thisConfig['Secrets']['SecretKey'] = configValue

	return thisConfig

def loadModule(thisConfig, logger, configParser):
	""" Load module config """
	try:
		with open(os.path.join(os.path.dirname(__file__), 'config', 'module.conf')) as f:
			configParser.readfp(f)
			configFilePath = "/secrets.conf"
	except IOError:
		configParser.read(os.path.join(os.path.dirname(__file__),"./config/module.conf"))
		configFilePath = os.path.join(os.path.dirname(__file__),"./config/module.conf")
		exit

	""" Collection point type """
	try:
		configValue=configParser.getboolean('ModuleConfig','collection_point_type')
	except:
		configValue = 'nfc_bcard_reader'
	logger.info("Collection point type : %s" % configValue)
	thisConfig['CollectionPointType'] = configValue

	""" Collection point id """
	try:
		configValue=configParser.getboolean('ModuleConfig','collection_point_id')
	except:
		configValue = 'nfc1'
	logger.info("Collection point ID : %s" % configValue)
	thisConfig['CollectionPointId'] = configValue

	""" Reader number """
	try:
		configValue=configParser.getint('ModuleConfig','reader_port_number')
	except:
		configValue = 0
	logger.info("Reader port number : %s" % configValue)
	thisConfig['ReaderPortNumber'] = configValue

	return thisConfig