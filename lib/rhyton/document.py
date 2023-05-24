"""
Module for modifying the rhino document.
This is the only module in this package that actually modifies a Rhino file.
"""
# python standard imports
import json
from contextlib import contextmanager
from collections import defaultdict

# rhino imports
import rhinoscriptsyntax as rs
from Rhino.Geometry import Line
import Rhino

# rhyton imports
from rhyton.main import Rhyton
from rhyton.utils import Format, toList, detectType


class ElementOverrides:
    """
    Class for handling color overrides on Rhino objects.
    """
    OVERRIDE_PROGRESS = "Color Overrides..."

    @classmethod
    def apply(cls, overrides):
        """
        Sets the colors for given elements. The original colors and color sources
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
        from rhyton.color import Color
        from rhyton.ui import ProgressBar

        overrides = toList(overrides)
        originalColors = DocumentConfigStorage().get(
                Rhyton().extensionOriginalColors, dict())

        with ProgressBar(len(overrides), label=cls.OVERRIDE_PROGRESS) as bar:
            for override in overrides:
                guids = override[Rhyton.GUID]
                guids = toList(guids)
                
                for guid in guids:
                    color = rs.ObjectColor(guid)
                    color = tuple([color[0], color[1], color[2]])
                    if not guid in originalColors:
                        original = dict()
                        original[Rhyton.COLOR] = Color.RGBtoHEX(color)
                        original[Rhyton.COLOR_SOURCE] = rs.ObjectColorSource(guid)
                        originalColors[guid] = original
                        
                    color = override.get(Rhyton.COLOR, Rhyton.HEX_WHITE)
                    rs.ObjectColor(
                            guid,
                            Color.HEXtoRGB(
                                    override.get(Rhyton.COLOR, Rhyton.HEX_WHITE)))
                bar.update()

        AffectedElements.save(Rhyton().extensionOriginalColors, originalColors)


    @classmethod
    def clear(cls, guids, clearSource=False):
        """
        Clear the color overrides for given objects.
        The original colors will be restored from the ``Document Text``.

        Args:
            guids (str): The ids of the objects.
            clearSource (bool, optional): If ``True``, the color source will be set to ``0``. Defaults to ``False``.
        """
        from rhyton.color import Color
        from rhyton.ui import ProgressBar

        originalColors = DocumentConfigStorage().get(
                Rhyton().extensionOriginalColors, defaultdict())
        
        with ProgressBar(len(guids), label=cls.OVERRIDE_PROGRESS) as bar:
            for guid in guids:
                hexColor = originalColors.get(guid, dict()).get(Rhyton.COLOR)
                if hexColor:
                    rgbColor = Color.HEXtoRGB(hexColor)
                    rs.ObjectColor(guid, rgbColor)

                if clearSource:
                    rs.ObjectColorSource(guid, originalColors.get(
                            guid, dict()).get(Rhyton.COLOR_SOURCE, 0))
                bar.update()

        AffectedElements.remove(Rhyton().extensionOriginalColors, guids)


class TextDot:
    """
    Class for handling Rhino text dot objects.
    """

    @staticmethod
    def add(data, valueKey, aggregate=True, prefixKey=None):
        """
        Adds a new text dot to the document.
        The textdot location is the center of the bounding box of given guid(s).
        Provide a list of guids, if you want to place the text dot
        in the middle of multiple objects.

        Note:
            The input dictionary can contain unrelated keys - they will be ignored.

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
        from rhyton.color import Color
        from rhyton.ui import ProgressBar

        data = toList(data)
        textDots = dict()
        with ProgressBar(len(data), label="Text Dots...") as bar:
            for dot in data:
                dot[Rhyton.GUID] = toList(dot[Rhyton.GUID])
                bBox = rs.BoundingBox(dot[Rhyton.GUID])
                if aggregate:
                    try:
                        value = ElementUserText.aggregate(
                                dot[Rhyton.GUID], valueKey)
                        value = Format.formatNumber(value, valueKey)
                    except:
                        value = len(dot[Rhyton.GUID])
                else:
                    value = ElementUserText.getValue(
                                dot[Rhyton.GUID][0], valueKey)
                    try:
                        value = Format.formatNumber(float(value), valueKey)
                    except:
                        if value == Rhyton.WHITESPACE:
                            value = Rhyton.EMPTY
                        elif value == None:
                            value = Rhyton.NOT_AVAILABLE

                if prefixKey:
                    value = "{}: {}".format(dot[prefixKey], value)

                point = Line(bBox[0], bBox[6]).PointAt(0.5)
                textDot = rs.AddTextDot(value, point)
                rs.ObjectColor(
                        textDot,
                        Color.HEXtoRGB(dot.get(Rhyton.COLOR, Rhyton.HEX_WHITE)))
                rs.TextDotFont(textDot, Rhyton.FONT)
                rs.TextDotHeight(textDot, 12.0)
                dot[Rhyton.GUID].append(str(textDot))
                textDots[str(textDot)] = 1
                bar.update()

        AffectedElements.save(Rhyton().extensionTextdots, textDots)
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
        self.storageName = Rhyton.RHYTON_CONFIG
        self.storage = dict()
        raw = rs.GetDocumentUserText(key=self.storageName)
        if raw and raw != Rhyton.WHITESPACE:
            self.storage = json.loads(raw)
        else:
            print("INFO: No configuration available.")

    def save(self, flag, data):
        """
        Saves the given data under the provided flag in the ``Rhino Document Text``.
        All data is saved inside the ``RHYTON_CONFIG`` field.
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
            keyPrefix (str, optional): The prefix for all keys. Defaults to "".
        """
        
        data = toList(data)

        for entry in data:
            guid = entry[Rhyton.GUID]
            del entry[Rhyton.GUID]
            for key, value in entry.items():
                key = Format.key(Rhyton.DELIMITER.join([Rhyton().extensionName, key]))
                rs.SetUserText(
                        guid,
                        key=key,
                        value=Format.value(value))

    @staticmethod
    def get(guids, keys=None):
        """
        Gets user text from given elements.

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
        keys = toList(keys)
        for guid in guids:
            if not keys: 
                keys = rs.GetUserText(guid)

            entry = dict()
            entry[Rhyton.GUID] = guid
            for key in keys:
                entry[key] = ElementUserText.getValue(guid, key)

            data.append(entry)
            
        return data
    
    @staticmethod
    def getKeys(guids):
        """
        Gets a complete set of unique user text keys from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
        """
        guids = toList(guids)
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
        guids = toList(guids)
        values = set()
        for guid in guids:
            if keys:
                for key in toList(keys):
                    value = ElementUserText.getValue(guid, key)
                    values.add(value)
            else:
                elementKeys = rs.GetUserText(guid)
                if elementKeys:
                    for key in elementKeys:
                        value = ElementUserText.getValue(guid, key)
                        values.add(value)
        
        return values
    
    @staticmethod
    def getValue(guid, key):
        """
        Wrapper function to get user text from an object

        Args:
            guid (str): A rhino objects id.
            key (str): The key to get the value from.

        Returns:
            mixed: None if key does not exist,
            " " if key has no value,
            else: str of value
        """

        # check if user text value is a rhino fuction value
        keyValue = ElementUserText.detectFunctionValue(rs.GetUserText(guid, key), guid)
        
        return detectType(keyValue)

    @staticmethod
    def aggregate(guids, keys=[]):
        """
        Aggregates user text values from given objects.
        Non-numeric values will cause an error.

        Args:
            guids (str): A list of Rhino objects ids.
            keys (list, optional): A list of keys. Defaults to [].

        Returns:
            float: The sum of all values.
        """
        keys = toList(keys)
        values = []
        for guid in guids:
            for key in keys:
                value = rs.GetUserText(guid, key)
                if value:
                    values.append(float(value))
        
        return sum(values)


    @staticmethod
    def remove(guids, keys):
        """
        Removes user text from given objects.

        Args:
            guids (str): A list of Rhino objects ids.
            keys (str): A list of keys.
        """
        guids = toList(guids)
        for guid in guids:
            for key in keys:
                rs.SetUserText(guid, key)

    @staticmethod
    def detectFunctionValue(uTxt, objID):
        """
        Detects if the value is calculated with a Rhino function

        Args:
            value (str): the string check
        Returns:
            value: converted or original value
        """
        if not uTxt:
            return uTxt
        if uTxt[:2] == "%<" and uTxt[-2:] == ">%":
            obj = rs.coercerhinoobject(objID)
            uTxt = Rhino.RhinoApp.ParseTextField(uTxt, obj, None)
        return uTxt

class Group:
    """
    Class for handling Rhino groups.
    """
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
        groupName = Rhyton.DELIMITER.join(
                [Rhyton.GROUP, str(groupName), str(uuid.uuid1())])
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


class Layer:
    """
    Class for handling layer information.
    """
    @classmethod
    @contextmanager
    def hierarchyInformation(cls, guids):
        """
        Context manager function to temporarlily add layer information to
        the user text of given Rhino objects.

        Args:
            guids (list(str)): A list of Rhino object ids.
        """
        layerHierachyDepth = cls.maxHierarchy(guids)
        cls.addLayerHierarchy(guids, layerHierachyDepth)
        try:
            yield
        finally:
            cls.removeLayerHierarchy(guids)

    @staticmethod
    def maxHierarchy(guids):
        """
        Gets the maximum depth of sublayers for the given list of objects.
        A simple layer return 1, a layer with one sublayer returns 2.

        Args:
            breps (list(str)): A list of Rhino object ids.

        Returns:
            int: The maximum depth of nested layers.
        """
        return max([len(rs.ObjectLayer(guid).split('::')) for guid in guids])
    
    @staticmethod
    def addLayerHierarchy(guids, depth):
        """
        Add the layer name for each depth level of sublayers to given entries.

        Args:
            data (dict): A dictionary or list of dictionaries.
            depth (int): The maximum depth of sublayer names to add.
        """
        from rhyton.ui import ProgressBar

        guids = toList(guids)

        with ProgressBar(len(guids), label="Adding Layer Information...") as bar:

            for guid in guids:
                data = dict()
                data[Rhyton.GUID] = guid
                objectLayer = rs.ObjectLayer(guid)
                fullHierarchy = Rhyton.DELIMITER.join([Rhyton.LAYER_HIERARCHY, Rhyton.NAME])
                data[fullHierarchy] = objectLayer
                layers = objectLayer.split('::')[:depth]
                for index, layer in enumerate(layers, 1):
                    key = Rhyton.DELIMITER.join([Rhyton.LAYER_HIERARCHY, str(index)])
                    data[key] = layer
            
                ElementUserText.apply(data)
                bar.update()
    
    @staticmethod
    def removeLayerHierarchy(guids):
        """
        Removes layer information from given objects user text.

        Args:
            guids (list(str)): A list of Rhino object ids.
        """
        keys =  ElementUserText.getKeys(guids)
        keys = [k for k in keys if Rhyton.LAYER_HIERARCHY in k]
        ElementUserText.remove(guids, keys)


def GetBreps(filterByTypes=[8, 16, 1073741824]):
    """
    Gets the currently selected Rhino objects or asks the user to go get some.
    
    Allowed objects are by default::

        8 = Surface
        16 = Polysurface
        8192 = Text Dot
        1073741824 = Extrusion

    Returns:
        list[str]: A list of Rhino objects ids.
    """
    selection = rs.GetObjects(preselect=True, select=True)
    if not selection:
        return None

    breps = [str(b) for b in selection if rs.ObjectType(b) in filterByTypes]
    return breps


def GetFilePath(ExtensionFilter):
    """
    Gets a file path from the user.

    Args:
        ExtensionFilter (str): The file extension filter.

    Returns:
        str: The file path.
    """
    return rs.OpenFileName(filter=ExtensionFilter)


def GetUnitSystem(abbreviate=False):
    """
    Gets the current Rhino units.

    Returns:
        str: The current Rhino units.
    """
    return rs.UnitSystemName(rs.UnitSystem(), abbreviate=abbreviate)