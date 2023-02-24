"""
Module for changing the document.
"""
import json

import rhinosciptsyntax as rs
from Rhino.Geometry import Line

from collections import defaultdict

from rhyton.utils import Key, Value, toList
from rhyton.color import Color


class ElementOverrides:
    """
    Class for handling color overrides on Rhino objects.
    """

    @staticmethod
    def apply(overrides):
        """
        Set the color for given elements. The original color and color source
        will be stored alongside the objects id in the document user text.
        When an objects is overridden by rhyton for a second time, 
        the original color and color source will remain as they are.

        Examples::

            ElementOverrides.apply(
                    [
                        {
                            "guid": [<guid1>, <guid2>],
                            "color": <hexvalue1>
                            },
                            {
                            "guid": <guid3>,
                            "color": <hexvalue2>
                        }
                    ])

            # or

            ElementOverrides.apply(
                    {
                        "guid": <guid>,
                        "color": <hexvalue>
                    })

        Args:
            overrides (list(dict)): A dictionary or a list of dictionaries.
        """
        originalColors = {}

        for override in overrides:
            guids = override['guid']
            guids = toList(guids)
            
            for guid in guids:
                original = {}
                original['source'] = rs.ObjectColorSource(guid)
                original['color'] = rs.ObjectColor(guid)
                originalColors[guid] = original
                rs.ObjectColor(
                        guid,
                        Color.HEXtoRGB(override['color']))

        AffectedElements.save('rhyton.originalColors', originalColors)


    @staticmethod
    def clear(guids):
        """
        Clear the color overrides for given objects.
        The original colors will be restored from the element's user text.

        Args:
            guids (str): The ids of the objects.
        """
        originalColors = DocumentConfigStorage().get('rhyton.originalColors')
        for guid in guids:
            rs.ObjectColor(guid, originalColors[guid]['color'])
            rs.ObjectColorSource(guid, originalColors[guid]['source'])

        AffectedElements.remove('rhyton.originalColors', guids)


class TextDot:
    """
    Class for handling Rhino text dot objects.
    """
    @staticmethod
    def add(data):
        """
        Adds a new text dot to the document.
        The textdot location is the center of the bounding box of given guid(s).
        Provide a list of guids, if you want to place the text dot
        in the middle of multiple objects.
        Hint: The input dictionary can contain unrelated keys - they will be ignored.
        This allows you to use the same input for ''TextDot.add'' and ''ElementOverrides.apply''

        Examples::

            TextDot.add(
                [
                    {
                        "guid": [<guid1>, <guid2>],
                        "value": <value1>,
                        "color": <color1>
                    },
                    {
                        "guid": <guid3>,
                        "value": <value2>,
                        "color": <color2>
                    }
                ])

            # or

            TextDot.add(
                    {
                        "guid": <guid>,
                        "value": <display value>,
                        "color": <display color>
                    })

        Args:
            dict (list(dict)): A dictionary or list of dictionaires.

        Returns:
            list: A list of the newly added text dots.
        """
        data = toList(data)
        for dot in data:
            bBox = rs.BoundingBox(dot['guid'])
            point = Line(bBox[0], bBox[6]).PointAt(0.5)
            textDot = rs.AddTextDot(dot['value'], point)
            rs.ObjectColor(
                    textDot,
                    Color.HEXtoRGB(dot['color']))
            rs.TextDotFont(textDot, 'Arial')
            rs.TextDotHeight(textDot, 12.0)
            dot['guid'].append(textDot)

        return data


class AffectedElements:
    """
    Class for handling information on the objects affected by rhyton.
    """
    @staticmethod
    def save(flag, data):
        """
        Saves the guids of given elements to the document user text.
        This allows rhyton to keep track of the elements it's modifying.

        The input 'data' should contain information on the previous or new state
        of the affected objects alongside their guid:

        Example::

            {<guid>: {'key1': 'value1'}}

        Args:
            flag (str): The identifier for the data.
            data (dict): A dictionary of guids with a dictionary as values.
        """
        existing = DocumentConfigStorage().get(flag, defaultdict())
        existing.update(data)
        DocumentConfigStorage().save(flag, existing)

    @staticmethod
    def remove(flag, guids):
        """
        Removes given guids from the document config storage saved under given flag.

        Args:
            guids (str): A single or a list of Rhino object ids.
        """
        guids = toList(guids)

        existing = DocumentConfigStorage().get(
                flag, defaultdict())
        for guid in guids:
            if guid in existing:
                del existing[guid]

        DocumentConfigStorage().save(flag, existing)


class DocumentConfigStorage:
    """
    Class for handling the reading and writing of document user text.
    """
    def __init__(self):
        self.storageName = 'RHYTON_CONFIG'
        self.storage = {}
        raw = rs.GetDocumentUserText(key=self.storageName)
        if raw:
            self.storage = json.loads(raw)

    @staticmethod
    def save(self, flag, data):
        """
        Saves the given data under the provided flag in the Rhino document user text.
        All data is saved inside the "RHYTON_CONFIG" field.
        The input data must be valid JSON.

        Args:
            flag (str): The identifier for the data.
            data (mixed): The data to store.
        """
        self.storage[flag] = data
        self.storage = {(k, v) for k, v in self.storage.iteritems() if v}
        raw = json.dumps(self.storage, sort_keys=True, ensure_ascii=False)
        rs.SetDocumentUserText(self.storageName, raw)
    
    def get(self, flag, default=None):
        """
        Gets the data stored under given flag.

        Example::

            config = rhyton.DocumentConfigStorage()
            item = config.get('name')

        Args:
            flag (str): The identifier for the data.
            default (mixed, optional): An optional default value. Defaults to None.

        Returns:
            mixed: The data stored under given flag.
        """
        return self.storage.get(flag, default)


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

        Examples::

            ElementUserText.apply(
                    [
                        {
                            "guid": [<guid1>, <guid2>],
                            "string_key": "Value",
                            "number_key": 0
                        },
                            {
                            "guid": <guid3>,
                            "string_key": "Value",
                            "number_key": 0
                        }
                    ])

            # or

            ElementUserText.apply(
                    {
                        "guid": <guid>,
                        "string_key": "Value",
                        "number_key": 0
                    })


        Due to Rhino's limitations, all values will be stored as strings.

        Args:
            data (list(dict)): A list of dictionaries describing the 
        """
        data = toList(data)

        guids =  set()
        for entry in data:
            guid = entry['guid']
            guids.add(guid)
            del entry['guid']
            for key, value in entry.items():
                rs.SetUserText(guid, Key(key), Value(value))

        AffectedElements.save('rhyton.usertextElements', guids)

    @staticmethod
    def get(guids, keys=None):
        """
        Gets the user text for given elements.

        Return format::

            [
                {
                    "guid": <guid1>, 
                    "example_key1": "example_value1"
                    "example_key2": "example_value2"
                }
            ]

        Args:
            guids (list(str)): A list of Rhino objects ids.
            keys (list(str), optional): A list of keys. By default, all keys are returned.

        Returns:
            list: A list of dictionaries.
        """
        data = []
        for guid in guids:
            if not keys: 
                keys = rs.GetUserText(guid)

            entry = {}
            entry['guid'] = guid
            for key in keys:
                entry[key] = rs.GetUserText(guid, key)
                data.append(entry)
        
        return data
    
    @staticmethod
    def getKeys(guids):
        """
        Gets a complete set of user text keys from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
        """
        guids = toList(guids)

        return (rs.GetUserText(guid) for guid in guids)
    
    @staticmethod
    def getValues(guids, fromKeys=[]):
        """
        Gets a complete set of user text values from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
        """
        guids = toList(guids)

        values = set()
        for guid in guids:
            if fromKeys:
                fromKeys = toList(fromKeys)
                for key in fromKeys:
                    values.add(rs.GetUserText(guid, key))
            else:
                keys = rs.GetUserText(guid)
                if keys:
                    for key in keys:
                        values.add(rs.GetUserText(guid, key))
        
        return values


class Group:

    @staticmethod
    def create(guids, groupName):
        """
        Creates a new group with given name and adds given objects to it.
        The groupname will be expanded to prevent ambiguity.

        Args:
            guids (str): A list or single Rhino object id.
            groupName (str): The basename of the group.
        """
        import uuid
        groupName = "_".join(['rhyton', groupName, str(uuid.uuid1())])
        rs.AddGroup(groupName)
        rs.AddObjectsToGroup(guids, groupName)
        return groupName

    @staticmethod
    def dissolve(guids):
        """
        Ungroups the guids' groups and then deletes the group definition.
        Delete all text dots among the guids in the process.

        Args:
            guids (str): A list or a single Rhino object id.
        """
        guids = toList(guids)
        groupNames = set()
        for guid in guids:
            groupNames.add(rs.ObjectTopGroup(guid))
            if rs.ObjectType(guid) == 8192:
                rs.DeleteObject(guid)
        
        for group in groupNames:
            rs.DeleteGroup(group)