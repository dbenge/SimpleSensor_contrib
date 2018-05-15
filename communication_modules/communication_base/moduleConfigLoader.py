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

    """ Big number threshold """
    try:
        configValue=configParser.getint('ModuleConfig','big_number_threshold')
    except:
        configValue = 11
    logger.info("Big number threshold: %s" % configValue)
    thisConfig['BigNumberThreshold'] = configValue