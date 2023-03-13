"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
# python standard imports
import os

# rhino imports
import rhinoscriptsyntax as rs

# rhyton imports
from main import Rhyton
from export import CsvExporter, JsonExporter
from document import GetBreps, ElementUserText, Group, TextDot
from document import DocumentConfigStorage, ElementOverrides, Layer
from utils import Format, groupGuidsBy

class Visualize(Rhyton):
    """
    Class for visualizing user text on Rhino objects.
    """
    @classmethod
    def byGroup(cls):
        """
        Visualizes a set of Rhino objects and their user text:
        The user input 'Parameter to Group By' is used for coloring
        and grouping objects, as well as for building sub-totals of the
        user-selected 'Parameter to Summarize'.
        Places text dots with the value for each group.
        """
        from color import ColorScheme

        breps = GetBreps()
        if not breps:
            return
        
        keys = ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(
                keys, message='Select Parameter to Group By:')
        if not selectedKey:
            return
        
        selectedValue = SelectionWindow.show(
                keys, message='Select Parameter to Summarize')
        if not selectedValue:
            return
        
        rs.EnableRedraw(False)
        objectData = ColorScheme.apply(breps, selectedKey)
        objectData = groupGuidsBy(objectData, [selectedKey, cls.COLOR])
        objectData = TextDot.add(objectData, selectedValue)
        for item in objectData:
            Group.create(item[cls.GUID], item[selectedKey])
        
        rs.UnselectAllObjects()
        rs.EnableRedraw(True)

    @classmethod
    def sumTotal(cls):
        from color import ColorScheme

        breps = GetBreps()
        if not breps:
            return
        
        keys = ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(
                keys, message='Select Parameter to Calculate Total:')
        if not selectedKey:
            return
        
        rs.EnableRedraw(False)
        objectData = {}
        objectData[cls.GUID] = breps
        objectData[cls.COLOR] = ColorScheme().getColors(1)[0]
        ElementOverrides.apply(objectData)
        objectData = TextDot.add(objectData, selectedKey)
        for item in objectData:
            Group.create(item[cls.GUID])
        
        rs.UnselectAllObjects()
        rs.EnableRedraw(True)

    @classmethod
    def byValue(cls):
        from color import ColorScheme

        breps = GetBreps()
        if not breps:
            return
    
        keys = ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(
                options=keys, message='Select Parameter to visualize:')
        if not selectedKey:
            return
        
        color = rs.GetColor(cls.STANDARD_COLOR_1)
        if not color:
            return
        
        colorStart = [color[0], color[1], color[2]]
        
        color = rs.GetColor(cls.STANDARD_COLOR_2)
        if not color:
            return    
        
        colorEnd = [color[0], color[1], color[2]]

        rs.EnableRedraw(False)
        objectData = ColorScheme.applyGradient(
                breps, selectedKey, [colorStart, colorEnd])
        objectData = TextDot.add(
                objectData, selectedKey, aggregate=False)
        for item in objectData:
            Group.create(item[cls.GUID])

        rs.UnselectAllObjects()
        rs.EnableRedraw(True)
    
    @classmethod
    def reset(cls):
        preSelection = rs.SelectedObjects()
        resetAll = 'select'
        if not preSelection:
            choices = {
                    "Yes, reset all.": 'reset',
                    "No wait, let me select!": 'select'}
            resetAll = SelectionWindow.show(
                    choices, message='Reset all visualizations?')

        if resetAll == 'select':
            breps = GetBreps(filterByTypes=[8, 16, 8192, 1073741824])
            if not breps:
                return
            
            rs.EnableRedraw(False)
            ElementOverrides.clear(breps)
            Group.dissolve(breps)
        elif resetAll == 'reset':
            rs.EnableRedraw(False)
            data = DocumentConfigStorage().get(
                    cls.EXTENSION_ORIGINAL_COLORS, dict())
            if not data:
                print('ERROR: No info about original colors available, select elements and try again.')

            guids = data.keys()
            Group.dissolve(guids)
            ElementOverrides.clear(guids)
            textDots = DocumentConfigStorage().get(
                    cls.EXTENSION_TEXTDOTS, dict()).keys()
            rs.DeleteObjects(textDots)
            DocumentConfigStorage().save(cls.EXTENSION_TEXTDOTS, None)

        rs.EnableRedraw(True)
    

class ColorSchemeEditor:
        # show dialog to pick from available color schemes
        # enter edit mode for selected color scheme
        # load button
        # export button
    
    @staticmethod
    def show():
        pass


class Export(Rhyton):

    def __init__(self):
        breps = GetBreps()
        if not breps:
            return
        
        exportMethod = SelectionWindow.show(
                [self.CSV, self.JSON],
                message='Select export format:')
        if not exportMethod:
            return
        
        layerHierachyDepth = Layer.maxHierarchy(breps)
        Layer.addLayerHierarchy(breps, layerHierachyDepth)
        keys = sorted(list(ElementUserText.getKeys(breps)))
        options = self.getCheckboxDefaults(keys)
        selectedOptions = SelectionWindow.showBoxes(options)
        if not selectedOptions:
            return
        
        self.setCheckboxDefaults(selectedOptions)
        selectedKeys = [key[0] for key in selectedOptions if key[1] == True]
        if exportMethod == self.CSV:
            self.toCSV(breps, selectedKeys)
        elif exportMethod == self.JSON:
            self.toJSON(breps, selectedKeys)

        Layer.removeLayerHierarchy(breps)

    def toCSV(self, guids, keys):
        data = ElementUserText.get(guids, keys)
        file = CsvExporter.write(data)
        os.startfile(file)

    def toJSON(self, guids, keys):
        data = ElementUserText.get(guids, keys)
        file = JsonExporter.write(data)
        os.startfile(file)

    def getCheckboxDefaults(self, keys):
        """
        Loads checkbox defaults from the document config storage for given keys.
        If no default is available in the document config storage, <True> will
        be used.

        Args:
            keys (list(str)): A list of keys to get default values for.

        Returns:
            tuple: A list of tuples indicating the defaults for given values.
        """
        checkboxSettingsFlag = '.'.join(
            [self.EXTENSION_NAME, self.EXPORT_CHECKBOXES])
        defaults = DocumentConfigStorage().get(
                checkboxSettingsFlag, dict())
        for key in keys:
            if not key in defaults:
                defaults[key] = True

        defaults = [(k, v) for k, v in defaults.items() if k in keys]
        return defaults

    def setCheckboxDefaults(self, newDefaults):
        """
        Updates the document config storage with new export checkbox defaults
        for the current extension.

        Args:
            defaults (tuple): A list of tuples indicating the default per value.
        """
        checkboxSettingsFlag = '.'.join(
            [self.EXTENSION_NAME, self.EXPORT_CHECKBOXES])
        defaults = DocumentConfigStorage().get(
                checkboxSettingsFlag, dict())
        newDefaults = dict((k, v) for k, v in newDefaults)
        defaults.update(newDefaults)
        DocumentConfigStorage().save(checkboxSettingsFlag, defaults)


class Settings(Rhyton):
    def __init__(self, extensionName):
        super(Settings, self).__init__(extensionName)
        """
        Inits a new Settings instance.
        Presents a UI to the user that shows the current settings and
        allows to change them.
        """
        inValidInput = True
        while inValidInput:
            res = SelectionWindow.dictBox(
                    options=self.settings, message=self.EXTENSION_SETTINGS)
            if res:
                try:
                    int(res[self.ROUNDING_DECIMALS_NAME])
                    inValidInput = False
                except:
                    pass
            else:
                inValidInput = False
        
        self.saveSettings(res)


class SelectionWindow:
    """
    Wrapper class for Rhino user interfaces.
    """
    @staticmethod
    def show(options, message=None):
        """
        Shows a list box to the user that allows to select from a
        list of options.

        Args:
            options (mixed): A list of strings or dict 
                    (shows keys to user, returns value).
            message (str, optional): The message to the user. Defaults to None.

        Returns:
            mixed: The value of the selected key from the input dictionary or 
                    the selected item from the input list.
        """
        if not type(options) == dict:
            options = dict((i, i) for i in options)

        res = rs.ListBox(options.keys(), message, default=options.keys()[0])
        if res:
            return options[res]
        
    @staticmethod
    def showBoxes(options, message=None):
        """
        Shows a checkbox list to the user that allows to select from
        multiple items.

        Example input/output::

            [("option1", True), ("option2", False)]

        The returns are formatted as shown above.

        Args:
            options (list(tuple)): A list of tuples with pre-defined checkbox states
            message (str, optional): The message to the user. Defaults to None.

        Returns:
            list(tuple): A list of tuples indicating
                    the name and state of each checkbox.
        """ 
        return rs.CheckListBox(options, message)
    
    @staticmethod
    def dictBox(options, message=None):
        """
        Show a dictionary-style list box to the user.

        Args:
            options (dict): The key, value pairs.
            message (str, optional): The message to the user. Defaults to None.
        """
        res = rs.PropertyListBox(
                [Format.value(k) for k in options.keys()],
                options.values(),
                message)
        if res:
            return dict((k, v) for k, v in zip(options.keys(), res))