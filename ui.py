"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
# python standard imports
import os
from datetime import datetime

# rhino imports
import rhinoscriptsyntax as rs

# rhyton imports
from main import Rhyton
from export import CsvExporter, JsonExporter
from document import GetBreps, ElementUserText, Group, TextDot, GetFilePath
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
        
        cls.reset()
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
        """
        Visualizes the total for selected parameter.
        Groups selected objects and places a text dot to display the total.
        Non-number parameter values will result in a simple object count.
        """
        from color import ColorScheme

        breps = GetBreps()
        if not breps:
            return
        
        keys = ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(
                keys, message='Select Parameter to Calculate Total:')
        if not selectedKey:
            return
        
        cls.reset()
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
        """
        Visualizes the value of selected parameter for each object individually.
        Applies a user-defined color gradient to the values.
        """
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

        cls.reset()
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
        """
        Resets the visualization for 'all' or 'selected' objects.
        Ungroups visualized objects.
        """
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
                    Rhyton().extensionOriginalColors, dict())
            if not data:
                print('ERROR: No info about original colors available, select elements and try again.')

            guids = data.keys()
            Group.dissolve(guids)
            ElementOverrides.clear(guids)
            textDots = DocumentConfigStorage().get(
                    Rhyton().extensionTextdots, dict()).keys()
            rs.DeleteObjects(textDots)
            DocumentConfigStorage().save(Rhyton().extensionTextdots, None)

        rs.EnableRedraw(True)
    

class ColorSchemeEditor(Rhyton):
    def __init__(self):
        from color import ColorScheme
        schemeName = self.showSchemes()
        if not schemeName:
            return
        
        keyValues = self.showColors(schemeName)
        if not keyValues:
            return
        
        ColorScheme().save(schemeName, keyValues)
    
    @classmethod
    def showSchemes(cls):
        from color import ColorScheme
        return SelectionWindow.show(
                ColorScheme().schemes.keys(), message="Select Color Scheme:")

    @classmethod
    def showColors(cls, schemeName):
        from color import ColorScheme
        scheme = ColorScheme().schemes.get(schemeName)
        return SelectionWindow.dictBox(scheme, message=schemeName)
    
    @staticmethod
    def importScheme():
        pass

    @staticmethod
    def exportScheme():
        pass


class Export(Rhyton):

    def __init__(self):
        """
        Inits a new export Instance. Asks the user to select the export format,
        gets memorized checkbox values for available keys. Presents those 
        to the user to select the keys for export. Stores checkbox states 
        and exports keys to selected output format.
        """
        breps = GetBreps()
        if not breps:
            return
        
        exportMethod = SelectionWindow.show(
                [self.CSV, self.JSON],
                message='Select export format:')
        if not exportMethod:
            return
        
        with Layer.hierarchyInformation(breps):
            flag = '.'.join([self.extensionName, self.EXPORT_CHECKBOXES])
            selectedKeys = self.getExportKeys(flag, breps)
            if not selectedKeys:
                return

            if exportMethod == self.CSV:
                self.toCSV(breps, selectedKeys)
            elif exportMethod == self.JSON:
                self.toJSON(breps, selectedKeys)

    def toCSV(self, guids, keys):
        """
        Exports the values for provided keys to CSV.
        Opens the new file.

        Args:
            guids (list(str)): A list of Rhino object ids.
            keys (list(str)): A list of document user text keys to export.
        """
        data = ElementUserText.get(guids, keys)
        file = CsvExporter.write(data)
        os.startfile(file)

    def toJSON(self, guids, keys):
        """
        Exports the values for provided keys to JSON.
        Opens the new file.

        Args:
            guids (list(str)): A list of Rhino object ids.
            keys (list(str)): A list of document user text keys to export.
        """
        data = ElementUserText.get(guids, keys)
        file = JsonExporter.write(data)
        os.startfile(file)

    @classmethod
    def getExportKeys(cls, flag, guids):
        """
        Presents a checkbox to the user to pick the user text keys for export.
        The checkbox states are stored in the document config storage and
        are used a the default values for the next time the dialog is shown.

        Args:
            flag (str): The identifier for the default values in the document config storage.
            guids (str): A list of Rhino object ids.

        Returns:
            list(str): A list of user text keys.
        """
        keys = sorted(list(ElementUserText.getKeys(guids)))
        options = cls.getCheckboxDefaults(flag, keys=keys)
        selectedOptions = SelectionWindow.showBoxes(options)
        if not selectedOptions:
            return
        
        cls.setCheckboxDefaults(flag, selectedOptions)
        selectedKeys = [key[0] for key in selectedOptions if key[1] == True]
        return selectedKeys

    @staticmethod
    def getCheckboxDefaults(flag, keys=[]):
        """
        Loads export checkbox defaults from the document config storage for given keys.
        If no default is available in the document config storage, <True> will
        be used.

        Args:
            flag (str): The identifier for the default values in the document config storage.
            keys (list(str)): A list of keys to get default values for.

        Returns:
            tuple: A list of tuples indicating the defaults for given values.
        """
        defaults = DocumentConfigStorage().get(flag, dict())
        if keys:
            for key in keys:
                if not key in defaults:
                    defaults[key] = True

            defaults = [(k, v) for k, v in defaults.items() if k in keys]
        else:
            defaults = [(k, v) for k, v in defaults.items()]

        return defaults

    @staticmethod
    def setCheckboxDefaults(flag, newDefaults):
        """
        Updates the document config storage with new export checkbox defaults
        for the current extension.

        Args:
            flag (str): The identifier for the default values in the document config storage.
            defaults (tuple): A list of tuples indicating the default per value.
        """
        defaults = DocumentConfigStorage().get(flag, dict())
        newDefaults = dict((k, v) for k, v in newDefaults)
        defaults.update(newDefaults)
        DocumentConfigStorage().save(flag, defaults)


class Settings(Rhyton):
    """
    Class for handling extension settings.
    """
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
                    options=self.settings, message=self.extensionSettings)
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

        res = rs.ListBox(sorted(options.keys()), message, default=options.keys()[0])
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
        return rs.CheckListBox(sorted(options), message)
    
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
        
    
class Powerbi(Rhyton):
    """
    Class for opening and updating PowerBI.
    """
    CUSTOM_TEMPLATE = "Load Custom Template"
    POWERBI_DATAFILE = Rhyton.HDM_DT_DIR + '/RhinoToolbarExtensions/powerbi.json'
    POWERBI_TEMPLATES_REPO = 'https://github.com/herzogdemeuron/powerbitemplates.git'
    POWERBI_TEMPLATES_DIR = Rhyton.HDM_DT_DIR + '/RhinoToolbarExtensions/powerbi-templates'
    POWERBI_TEMPLATES_EXTENSION = '.pbit'
    TIMESTAMP = "timestamp"
    # fixed keys are necessary to ensure the powerbi visuals do not break
    VIZ_KEY = "visualization_parameter"
    POWERBI_TEMPLATE = '.template'

    @classmethod
    def show(cls):
        pbiRunning = cls._processExists('PBIDesktop.exe')
        if pbiRunning:
            print("powerbi already running")
            return
        
        template = cls._pickTemplate()
        if not template:
            return
        
        config = dict()
        config[cls.POWERBI_TEMPLATE] = template
        if template == cls.CUSTOM_TEMPLATE:
            template = GetFilePath(cls.POWERBI_TEMPLATES_EXTENSION)
            breps = GetBreps()
            if not breps:
                return
        
            data = cls._getData(breps)
            if not data:
                return
        else:
            breps = GetBreps()
            if not breps:
                return
        
            allKeys = ElementUserText.getKeys(breps)
            vizKey = SelectionWindow.show(allKeys, message="Select Parameter to Visualize:")
            config[cls.VIZ_KEY] = vizKey
            fixedKeys = cls.fixedKeys()
            fixedKeys.append(vizKey)
            data = cls._getData(breps, fixedKeys=fixedKeys, vizKey=vizKey)
            if not data:
                return

        templateFlag = Rhyton().extensionName + cls.POWERBI + cls.POWERBI_TEMPLATE
        DocumentConfigStorage().save(templateFlag, config)

        JsonExporter.write(data, file=cls.POWERBI_DATAFILE)
        os.startfile(template)
        
    @classmethod
    def update(cls):
        templateFlag = Rhyton().extensionName + cls.POWERBI + cls.POWERBI_TEMPLATE
        config = DocumentConfigStorage().get(templateFlag)
        if config[cls.POWERBI_TEMPLATE] == cls.CUSTOM_TEMPLATE:
            breps = GetBreps()
            if not breps:
                return
        
            data = cls._getData(breps)
            if not data:
                return
        else:
            breps = GetBreps()
            if not breps:
                return
        
            vizKey = config.get(cls.VIZ_KEY)
            fixedKeys = cls.fixedKeys()
            fixedKeys.append(vizKey)
            data = cls._getData(breps, fixedKeys=fixedKeys, vizKey=vizKey)
            if not data:
                return
            
        JsonExporter.append(data, cls.POWERBI_DATAFILE)

    @classmethod
    def undoUpdate(cls):
        pass

    @classmethod
    def _pickTemplate(cls):
        if not os.path.exists(cls.POWERBI_TEMPLATES_DIR):
            os.makedirs(cls.POWERBI_TEMPLATES_DIR)

        files = cls.absoluteFilePaths(cls.POWERBI_TEMPLATES_DIR)
        templates = [os.path.abspath(f) for f in files if f.endswith(cls.POWERBI_TEMPLATES_EXTENSION)]
        templateNames = [os.path.basename(t).replace(cls.POWERBI_TEMPLATES_EXTENSION, '') for t in templates]
        options = dict((k, v) for k, v in zip(templateNames, templates))
        options[cls.CUSTOM_TEMPLATE] = cls.CUSTOM_TEMPLATE
        return SelectionWindow.show(options, message="Pick PowerBI Template:")

    @classmethod
    def _getData(cls, guids, fixedKeys=[], vizKey=None):
        with Layer.hierarchyInformation(guids):
            flag = '.'.join([Rhyton().extensionPowerbi, cls.EXPORT_CHECKBOXES])
            if fixedKeys:
                selectedKeys = fixedKeys
            else:
                selectedKeys = Export.getExportKeys(flag, guids)
                if not selectedKeys:
                    return

            data = ElementUserText.get(guids, selectedKeys)

        timeStamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        prefix = Rhyton().extensionName + cls.DELIMITER
        for d in data:
            if vizKey and vizKey in d:
                d[cls.VIZ_KEY] = d.pop(vizKey)

            for key in d.keys():
                if Rhyton().extensionName in key:
                    keyNew = key.replace(prefix, '')
                    d[keyNew] = d.pop(key)
            d[cls.TIMESTAMP] = timeStamp

        return data
    
    @staticmethod
    def _processExists(processName):
        import subprocess
        # checks if a process is running or not
        call = 'TASKLIST', '/FI', 'imagename eq %s' % processName
        # use buildin check_output right away
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(call).decode()
        # check in last line for process name
        lastLine = output.strip().split('\r\n')[-1]
        # because Fail message could be translated
        return lastLine.lower().startswith(processName.lower())
    
    @staticmethod
    def absoluteFilePaths(directory):
        for dirpath,_,filenames in os.walk(directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(dirpath, f))

    @classmethod
    def fixedKeys(cls):
        """
        Generates fixed keys when needed. This cannot be done as a
        class variable because the extension name might change 

        Yields:
            _type_: _description_
        """
        name = Rhyton().extensionName
        return [
            cls.DELIMITER.join([name, cls.LAYER_HIERARCHY, cls.NAME]),
            cls.DELIMITER.join([name, cls.LAYER_HIERARCHY, "1"]),
            cls.DELIMITER.join([name, cls.LAYER_HIERARCHY, "2"]),
            cls.DELIMITER.join([name, cls.LAYER_HIERARCHY, "3"])]