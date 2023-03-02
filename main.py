class Rhyton(object):
    """
    Base class to provide a shared data environment between sub-classes.
    This is particularly useful share extension specific settings across all 
    of self's classes while maintaining a single point of entry for developers
    using self as a base of their extension.

    Instead of having a variables.py, this class 
    contains all module-wide variables.

    The init of this class is typically called when instanciating a sub-class.
    The classes in the 'ui' module are a good example of this.

    Example::

        self.Visualize('<name_of_extension>').byGroup()

    This will trigger Rhyton to load the settings for the specified extension
    and provide them as a class variable.

    .. note::

        Create a Rhyton instance and provide you extension name 
        before using any other self functionality.
    """

    RHYTON_CONFIG = 'RHYTON_CONFIG'
    RHYTON_GROUP = 'self.group'
    TEXTDOTS = 'self.textdots'
    ORIGINAL_COLORS = 'self.originalColors'
    COLOR_SCHEMES = 'self.colorschemes'
    DOT_SETTINGS = '.settings'
    DELIMITER = "_"
    WHITESPACE = " "
    KEY_PREFIX_NAME = 'keyPrefix'
    UNIT_SUFFIX_NAME = 'unitSuffix'
    ROUNDING_DECIMALS_NAME = 'roundingDecimals'
    GUID = "guid"
    COLOR = 'color'
    COLOR_SOURCE = 'colorSource'
    EMPTY = "<empty>"
    NOT_AVAILABLE = "n/a"
    STANDARD_COLOR_1 = (200,200,255)
    STANDARD_COLOR_2 = (50,50,255)
    HEX_WHITE = '#FFFFFF'
    CSV = "CSV"
    JSON = "JSON"
    FONT = 'Arial'
    NAME = 'name'


    def __init__(self, extensionName):
        """
        Inits a new Rhyton instance and loads the settings for given extension.
        Adds some shorthands to the settings as class variables.

        Args:
            extensionName (str): The name of the extension that is calling Rhyton.
        """
        self.extensionName = extensionName
        Rhyton.settings = self.getSettings()
        Rhyton.KEY_PREFIX = Rhyton.settings[self.KEY_PREFIX_NAME]
        Rhyton.UNIT_SUFFIX = Rhyton.settings[self.UNIT_SUFFIX_NAME]
        Rhyton.ROUNDING_DECIMALS = Rhyton.settings[self.ROUNDING_DECIMALS_NAME]
    
    def saveSettings(
            self,
            keyPrefix="ry_",
            unitSuffix="m",
            roundingDecimals=2):
        """
        Saves a configuration to the document text.

        Args:
            extensionName (str): The extension name.
            keyPrefix (str, optional): The prefix for every key. Defaults to "ry_".
            unitSuffix (str, optional): The units suffix for display. Defaults to "m".
            roundingDecimals (int, optional): The rounding precision for display values. Defaults to 2.
        """
        import document
        settings = self.generateSettings(keyPrefix, unitSuffix, roundingDecimals)
        document.DocumentConfigStorage().save(
                self.extensionName + self.DOT_SETTINGS, settings)
    
    def getSettings(self):
        """
        Gets a settings configuration from the document text.

        Args:
            extensionName (str, optional): The name of the extension. Defaults to 'self'.

        Returns:
            dict: The configuration.
        """
        import document
        config = document.DocumentConfigStorage().get(
                self.extensionName + self.DOT_SETTINGS, None)
        if config:
            return config
        else:
            return self.generateSettings()

    def generateSettings(self, keyPrefix="ry_", unitSuffix="m", roundingDecimals=2):
        """
        Generates a settings configuration.

        Args:
            keyPrefix (str, optional): The prefix to use before every key. Defaults to "".
            unitSuffix (str, optional): The unit suffix. Defaults to "".
            roundingDecimals (int, optional): The rounding precision for display values. Defaults to 2.

        Returns:
            dict: The resulting configuration.
        """
        config = dict()
        config[self.KEY_PREFIX_NAME] = keyPrefix
        config[self.UNIT_SUFFIX_NAME] = unitSuffix
        config[self.ROUNDING_DECIMALS_NAME] = roundingDecimals
        return config