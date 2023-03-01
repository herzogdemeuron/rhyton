"""
Module for changing the document.
"""
import json

import rhinoscriptsyntax as rs
import rhyton

from Rhino.Geometry import Line

from collections import defaultdict



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
        overrides = rhyton.toList(overrides)
        originalColors = dict()

        for override in overrides:
            guids = override['guid']
            guids = rhyton.toList(guids)
            
            for guid in guids:
                color = rs.ObjectColor(guid)
                color = tuple([color[0], color[1], color[2]])
                original = dict()
                original['color'] = rhyton.Color.RGBtoHEX(color)
                original['source'] = rs.ObjectColorSource(guid)
                originalColors[guid] = original
                rs.ObjectColor(
                        guid,
                        rhyton.Color.HEXtoRGB(override.get('color', '#FFFFFF')))

        AffectedElements.save('rhyton.originalColors', originalColors)


    @staticmethod
    def clear(guids):
        """
        Clear the color overrides for given objects.
        The original colors will be restored from the element's user text.

        Args:
            guids (str): The ids of the objects.
        """
        originalColors = DocumentConfigStorage().get(
                'rhyton.originalColors', defaultdict())
        for guid in guids:
            hexColor = originalColors.get(guid, dict()).get('color')
            if hexColor:
                rgbColor = rhyton.Color.HEXtoRGB(hexColor)
                rs.ObjectColor(guid, rgbColor)

            rs.ObjectColorSource(guid, originalColors.get(
                    guid, dict()).get('source', 0))

        AffectedElements.remove('rhyton.originalColors', guids)


class TextDot:
    """
    Class for handling Rhino text dot objects.
    """
    @staticmethod
    def add(data, valueKey):
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
                        "color": <color1>
                    },
                    {
                        "guid": <guid3>,
                        "color": <color2>
                    }
                ])

            # or

            TextDot.add(
                    {
                        "guid": <guid>,
                        "color": <display color>
                    })

        Args:
            dict (list(dict)): A dictionary or list of dictionaires.
            valueKey (str): The key to aggregate or count values.
            prefix (str, optional): The text to display before the value.

        Returns:
            list: The input list of dicts with the guids of the text dots added.
        """
        data = rhyton.toList(data)
        textDots = {}
        for dot in data:
            dot['guid'] = rhyton.toList(dot['guid'])
            bBox = rs.BoundingBox(dot['guid'])
            try:
                value = ElementUserText.aggregate(dot['guid'], valueKey)
                value = rhyton.formatNumber(value)
            except:
                value = len(dot['guid'])

            # textValues = [prefix, value]
            # if showGroupName:
            #     textValues.insert(1, dot[groupKey])

            # text = " ".join(textValues).strip()
            point = Line(bBox[0], bBox[6]).PointAt(0.5)
            textDot = rs.AddTextDot(value, point)
            rs.ObjectColor(
                    textDot,
                    rhyton.Color.HEXtoRGB(dot.get('color', '#FFFFFF')))
            rs.TextDotFont(textDot, 'Arial')
            rs.TextDotHeight(textDot, 12.0)
            dot['guid'].append(str(textDot))
            textDots[str(textDot)] = 1

        AffectedElements.save('rhyton.textdots', textDots)
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
        guids = rhyton.toList(guids)

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
        self.storage = dict()
        raw = rs.GetDocumentUserText(key=self.storageName)
        if raw and raw != ' ':
            self.storage = json.loads(raw)
        else:
            print('No configuration available.')

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
        self.storage = dict((k, v) for k, v in self.storage.iteritems() if v)
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
        data = rhyton.toList(data)

        # guids =  set()
        for entry in data:
            guid = entry['guid']
            # guids.add(guid)
            del entry['guid']
            for key, value in entry.items():
                rs.SetUserText(guid, rhyton.Key(key), rhyton.Value(value))

        # AffectedElements.save('rhyton.usertextElements', guids)

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

            keys = rhyton.toList(keys)
            entry = dict()
            entry['guid'] = guid
            for key in keys:
                entry[key] = rs.GetUserText(guid, key)
                data.append(entry)
        return data
    
    @staticmethod
    def getKeys(guids):
        """
        Gets a complete set of unique user text keys from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
        """
        guids = rhyton.toList(guids)
        keys = set()
        for guid in guids:
            for key in rs.GetUserText(guid):
                keys.add(key)

        return keys
    
    @staticmethod
    def getValues(guids, keys=[]):
        """
        Gets a complete set of unique user text values from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
        """
        guids = rhyton.toList(guids)
        values = set()
        for guid in guids:
            if keys:
                for key in rhyton.toList(keys):
                    values.add(rs.GetUserText(guid, key))
            else:
                elementKeys = rs.GetUserText(guid)
                if elementKeys:
                    for key in elementKeys:
                        values.add(rs.GetUserText(guid, key))
        
        return values
    
    @staticmethod
    def aggregate(guids, keys=[]):
        keys = rhyton.toList(keys)
        values = []
        for guid in guids:
            for key in keys:
                value = rs.GetUserText(guid, key)
                if value:
                    values.append(float(value))
        
        return sum(values)


class Group:

    @staticmethod
    def create(guids, groupName=''):
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
        guids = rhyton.toList(guids)
        groupNames = set()
        for guid in guids:
            groupNames.add(rs.ObjectTopGroup(guid))
            if rs.ObjectType(guid) == 8192:
                rs.DeleteObject(guid)
        
        for group in groupNames:
            rs.DeleteGroup(group)