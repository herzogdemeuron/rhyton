"""
Module for changing the document.
"""

class ElementOverrides:
    """
    Class for handling color overrides on Rhino objects.
    """

    @staticmethod
    def apply(overrides):
        """
        Set the color for given elements. The original color will be stored
        in the element's user text.

        An override is specified as:

            {"guid": <guid>, "color": <hex value>}

        Args:
            overrides (list(dict)): The colors for the elements.
        """
        pass

    @staticmethod
    def clear(elements):
        """
        Clear the color overrides for given elements.
        The original colors will be restored from the element's user text.

        Args:
            elements (_type_): _description_
        """
        pass


class TextDot:
    """
    Class for handling Rhino text dot objects.
    """
    @staticmethod
    def add(tuple):
        """
        Adds a new text dot to the document.

        Args:
            tuple (tuple): A 3-fold tuple: (location, value, color)
        """
        pass


class AffenctedElements:
    """
    Class for handling information on the objects affected by rhyton.
    """
    @staticmethod
    def save(guids):
        """
        Saves the guids of given elements to the document user text.
        This allows rhyton to keep track of the elements it's modifying.

        Args:
            guids (list(str)): A list of Rhino object ids.
        """
        pass

    @staticmethod
    def remove(guids):
        """
        Removes given guids from the list of saved guid in the
        document user text. 

        Args:
            guids (list(str)): A list of Rhino object ids.
        """
        pass


class DocumentUserText:
    """
    Class for handling the reading and writing of document user text.
    """
    @staticmethod
    def save(flag, data):
        """
        Saves the given data under the provided flag in the Rhino document user text.
        All data is saved inside the "rhyton" field.
        The input data must be valid JSON.

        Args:
            flag (str): The identifier for the data.
            data (mixed): The data to store.
        """
        pass
    
    @staticmethod
    def get(flag):
        """
        Gets the data stored with given flag from the Rhino document user text.

        Args:
            flag (str): The identifier for the data.
        """
        pass


class ElementUserText:
    """
    Class for handling user text on Rhino objects.
    """
    @staticmethod
    def apply(data):
        """
        Applies given user text to provided elements.
        The expected input format for 'data' is a dictionary containing the guid
        as well as at least one user text key:

            {"guid": <guid>, "string_key": "Value", "number_key": 0}

        Due to Rhino's limitations, all values will be stored as strings.

        Args:
            data (list(dict)): A list of dictionaries describing the 
        """
        # value = rhyton.Value(value)
        # key = rhyton.Key(key)
        pass
    
    @staticmethod
    def get(guids, keys=[]):
        """
        Gets the user text for given elements.

        Args:
            guids (list(str)): A list of Rhino objects ids.
            keys (list(str), optional): A list of keys. By default, all keys are returned.
        """
        # key = rhyton.Key(key)
        # get user text
        # format for {guid: 123, key:value}
        # return list(dict)
        pass


class Group:

    @staticmethod
    def create(guids):
        pass

    @staticmethod
    def expolode(groupIdentifier):
        pass