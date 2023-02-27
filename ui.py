"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
import os
import rhinoscriptsyntax as rs
import export
import rhyton
from collections import defaultdict 


class Visualization:

    @staticmethod
    def byGroup():
        breps = rhyton.GetBreps()
        if not breps:
            return
        
        keys = rhyton.ElementUserText.getKeys(breps)
        keys.add("bl_grand_total")
        selectedKey = SelectionWindow.show(keys, message='Select Parameter to Group By:')
        if not selectedKey:
            return
        
        keys.remove("bl_grand_total")
        selectedValue = SelectionWindow.show(keys, message='Select Parameter to Summarize')
        if not selectedValue:
            return
        
        rs.EnableRedraw(False)
        objectData = rhyton.ColorScheme.apply(breps, selectedKey)
        objectData = rhyton.groupGuidsBy(objectData, [selectedKey, 'color'])
        objectData = rhyton.TextDot.add(
                objectData, selectedKey, selectedValue)
        for item in objectData:
            rhyton.Group.create(item['guid'], item[selectedKey])
        
        rs.UnselectAllObjects()
        rs.EnableRedraw(True)

    @staticmethod
    def byValue():
        breps = rhyton.GetBreps()
        if not breps:
            return
    
        keys = rhyton.ElementUserText.getKeys(breps)
        selectedKey = SelectionWindow.show(keys, message='Select Parameter to visualize:')
        if not selectedKey:
            return
        
        objectData = rhyton.ColorScheme.applyGradient(breps, selectedKey)
        objectData = rhyton.groupGuidsBy(objectData, [selectedKey, 'color'])
        objectData = rhyton.TextDot.add(objectData)
        for item in objectData:
            rhyton.Group.create(item['guid'], item[selectedKey])
    
    @staticmethod
    def reset():
        preSelection = rs.SelectedObjects()
        resetAll = 'select'
        if not preSelection:
            choices = {
                    "Yes, reset all.": 'reset',
                    "No wait, let me select!": 'select'}
            resetAll = SelectionWindow.show(
                    choices, message='Reset all visualizations?')

        rs.EnableRedraw(False)
        if resetAll == 'reset':
            data = rhyton.DocumentConfigStorage().get(
                    'rhyton.originalColors', dict())
            if not data:
                print('ERROR: No info about original colors available, select elements and try again.')

            guids = data.keys()
            rhyton.Group.dissolve(guids)
            rhyton.ElementOverrides.clear(guids)
            textDots = rhyton.DocumentConfigStorage().get(
                    'rhyton.textdots', dict()).keys()
            rs.DeleteObjects(textDots)
            rhyton.AffectedElements.remove('rhyton.textdots', textDots)
        elif resetAll == 'select':
            breps = rhyton.GetBreps(filterByTypes=[8, 16, 8192, 1073741824])
            if not breps:
                return
            
            rhyton.ElementOverrides.clear(breps)
            rhyton.Group.dissolve(breps)

        rs.EnableRedraw(True)
    
    @staticmethod
    def export():
        breps = rhyton.GetBreps()
        if not breps:
            return
        
        CSV, JSON = "CSV", "JSON"
        exportMethod = SelectionWindow.show(
                [CSV, JSON],
                message='Select export format:')
        keys = rhyton.ElementUserText.getKeys()
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
        data = rhyton.ElementUserText.get(guids, keys)
        file = export.CSV.write(data)
        os.startfile(file)

    @staticmethod
    def toJSON(guids, keys):
        data = rhyton.ElementUserText.get(guids, keys)
        file = export.JSON.write(data)
        os.startfile(file)


class SelectionWindow:

    @staticmethod
    def show(options, message=None):
        if not type(options) == dict:
            options = dict((i, i) for i in options)

        res = rs.ListBox(options.keys(), message)
        if res:
            return options[res]
        
    @staticmethod
    def showBoxes(options, message=None):
        if not type(options) == tuple:
            options = tuple((i, True) for i in options)

        return rs.CheckListBox(options, message)