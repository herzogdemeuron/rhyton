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
from document import DocumentConfigStorage, ElementOverrides
from color import ColorScheme
from utils import groupGuidsBy, Format

class Visualize(Rhyton):
    def __init__(self, extensionName):
        super(Visualize, self).__init__(extensionName)

    def byGroup(self):
        """
        Visualizes a set of Rhino objects and their user text:
        The user input 'Parameter to Group By' is used for coloring
        and grouping objects, as well as for building sub-totals of the
        user-selected 'Parameter to Summarize'.
        Places text dots with the value for each group.
        """
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
        objectData = groupGuidsBy(objectData, [selectedKey, self.COLOR])
        objectData = TextDot.add(objectData, selectedValue)
        for item in objectData:
            Group.create(item[self.GUID], item[selectedKey])
        
        rs.UnselectAllObjects()
        rs.EnableRedraw(True)

    def sumTotal(self):
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
        objectData[self.GUID] = breps
        objectData[self.COLOR] = ColorScheme().getColors(1)[0]
        ElementOverrides.apply(objectData)
        objectData = TextDot.add(objectData, selectedKey)
        for item in objectData:
            Group.create(item[self.GUID])
        
        rs.UnselectAllObjects()
        rs.EnableRedraw(True)

    def byValue(self):
        breps = GetBreps()
        if not breps:
            return
    
        keys = ElementUserText.getKeys(breps)
        options = dict((Format.value(k), k) for k in keys)
        selectedKey = SelectionWindow.show(
                options, message='Select Parameter to visualize:')
        if not selectedKey:
            return
        
        color = rs.GetColor(self.STANDARD_COLOR_1)
        if not color:
            return
        
        colorStart = [color[0], color[1], color[2]]
        
        color = rs.GetColor(self.STANDARD_COLOR_2)
        if not color:
            return    
        
        colorEnd = [color[0], color[1], color[2]]

        rs.EnableRedraw(False)
        objectData = ColorScheme.applyGradient(
                breps, selectedKey, [colorStart, colorEnd])
        objectData = TextDot.add(
                objectData, selectedKey, aggregate=False)
        for item in objectData:
            Group.create(item[self.GUID])

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
                    cls.ORIGINAL_COLORS, dict())
            if not data:
                print('ERROR: No info about original colors available, select elements and try again.')

            guids = data.keys()
            Group.dissolve(guids)
            ElementOverrides.clear(guids)
            textDots = DocumentConfigStorage().get(
                    cls.TEXTDOTS, dict()).keys()
            rs.DeleteObjects(textDots)
            DocumentConfigStorage().save(cls.TEXTDOTS, None)

        rs.EnableRedraw(True)
    

class ColorSchemeEditor:
        # show dialog to pick from available color schemes
        # enter edit mode for selected color scheme
        # load button
        # export button
    
    @staticmethod
    def show():
        pass


class Export:

    def __init__(self):
        breps = GetBreps()
        if not breps:
            return
        
        exportMethod = SelectionWindow.show(
                [self.CSV, self.JSON],
                message='Select export format:')
        keys = ElementUserText.getKeys()
        # add memory to remember state of checkboxes
        selectedKeys = SelectionWindow.showBoxes(keys)

        if exportMethod == self.CSV:
            Export.toCSV(breps, selectedKeys)
        elif exportMethod == self.JSON:
            exportMethod.toJSON(breps, selectedKeys)

    def toCSV(self, guids, keys):
        data = ElementUserText.get(guids, keys)
        file = CsvExporter.write(data)
        os.startfile(file)

    def toJSON(self, guids, keys):
        data = ElementUserText.get(guids, keys)
        file = JsonExporter.write(data)
        os.startfile(file)


class SelectionWindow:

    @staticmethod
    def show(options, message=None):
        if not type(options) == dict:
            options = dict((i, i) for i in options)

        res = rs.ListBox(options.keys(), message, default=options.keys()[0])
        if res:
            return options[res]
        
    @staticmethod
    def showBoxes(options, message=None):
        if not type(options) == tuple:
            options = tuple((i, True) for i in options)

        return rs.CheckListBox(options, message)