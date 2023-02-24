"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
import os
import rhinoscriptsyntax as rs
import export
from utils import GetBreps, groupGuidsBy
from document import ElementUserText, TextDot, Group, ElementOverrides
from document import DocumentConfigStorage
from color import ColorScheme



class Visualization:

    @staticmethod
    def byGroup():
        breps = GetBreps()
        keys = ElementUserText.getKeys(breps)
        keys.add("grand_total")
        selectedKey = SelectionWindow.show(keys, message='Select Parameter to group by:')
        if not selectedKey:
            return
        
        objectData = ColorScheme.apply(breps, selectedKey)
        objectData = groupGuidsBy(objectData, [selectedKey, 'color'])
        objectData = TextDot.add(objectData)
        for item in objectData:
            Group.create(item['guid'], item[selectedKey])

    @staticmethod
    def byValue():
        breps = GetBreps()
        keys = ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(keys, message='Select Parameter to visualize:')
        if not selectedKey:
            return
        
        objectData = ColorScheme.applyGradient(breps, selectedKey)
        objectData = groupGuidsBy(objectData, [selectedKey, 'color'])
        objectData = TextDot.add(objectData)
        for item in objectData:
            Group.create(item['guid'], item[selectedKey])
    
    @staticmethod
    def reset():
        preSelection = rs.SelectedObjects()
        if not preSelection:
            choices = {
                    "Yes, reset all.": True, "No wait, let me select!": False}
            resetAll = SelectionWindow.show(
                    choices, message='Reset all visualizations?')

        if resetAll:
            data = DocumentConfigStorage().get('rhyton.originalColors')
            guids = set(d['guid'] for d in data)
            Group.dissolve(guids)
            ElementOverrides.clear(guids)
        elif not resetAll:
            breps = GetBreps()
            Group.dissolve(breps)
            ElementOverrides.clear(breps)
    
    @staticmethod
    def export():
        breps = GetBreps()
        CSV, JSON = "CSV", "JSON"
        exportMethod = SelectionWindow.show(
                [CSV, JSON],
                message='Select export format:')
        keys = ElementUserText.getKeys()
        # add memory to remember state of checkboxes
        selectedKeys = SelectionWindow.showBoxes(keys)

        if exportMethod == CSV:
            Export.toCSV(breps, selectedKeys)
        elif exportMethod == JSON:
            exportMethod.toJSON(breps, selectedKeys)
        

class ColorSchemeEditor:
        # show dialog to pick from available color schemes
        # enter edit mode for selected color scheme
        # load button
        # export button
    
    @staticmethod
    def show():
        pass


class Export:

    @staticmethod
    def toCSV(guids, keys):
        data = ElementUserText.get(guids, keys)
        file = export.CSV.write(data)
        os.startfile(file)

    @staticmethod
    def toJSON(guids, keys):
        data = ElementUserText.get(guids, keys)
        file = export.JSON.write(data)
        os.startfile(file)


class SelectionWindow:

    @staticmethod
    def show(options, message=None):
        if not type(options) == dict:
            options = {(i, i) for i in options}

        res = rs.ListBox(options.keys(), message)
        if res:
            return options[res]
        
    @staticmethod
    def showBoxes(options, message=None):
        if not type(options) == tuple:
            options = tuple((i, True) for i in options)

        return rs.CheckListBox(options, message)