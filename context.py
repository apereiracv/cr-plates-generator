import configparser

class Context(object):
    """Contains execution information and configuration general to all the application"""

    def __init__(self, configurationPath):
        self.configuration = None
        self.configurationPath = None
        self.loadConfig(configurationPath)

    def setConfig(self, section, key, value):
        self.configuration.set(section, key, value)

    def getConfig(self, section, key):
        return self.configuration.get(section, key)

    def getBoolean(self, section, key):
        return self.configuration.getboolean(section, key)

    def saveConfig(self):
        with open(self.configurationPath, 'w') as configFile:
            self.configuration.write(configFile)

    def loadConfig(self, configurationPath):
        self.configuration = configparser.ConfigParser()
        self.configurationPath = configurationPath
        with open(configurationPath) as configFile:
            self.configuration.readfp(configFile)
        
