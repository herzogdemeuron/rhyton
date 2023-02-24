"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
import os
import rhinoscriptsyntax as rs
import export
import rhyton


class Visualization:

    @staticmethod
    def byGroup():
        breps = rhyton.GetBreps()
        keys = rhyton.ElementUserText.getKeys(breps)
        keys.add("grand_total")
        selectedKey = SelectionWindow.show(keys, message='Select Parameter to group by:')
        if not selectedKey:
            return
        
        objectData = rhyton.ColorScheme.apply(breps, selectedKey)
        objectData = rhyton.groupGuidsBy(objectData, [selectedKey, 'color'])
        objectData = rhyton.TextDot.add(objectData)
        for item in objectData:
            rhyton.Group.create(item['guid'], item[selectedKey])

    @staticmethod
    def byValue():
        breps = rhyton.GetBreps()
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
        if not preSelection:
            choices = {
                    "Yes, reset all.": True, "No wait, let me select!": False}
            resetAll = SelectionWindow.show(
                    choices, message='Reset all visualizations?')

        if resetAll:
            data = rhyton.DocumentConfigStorage().get('rhyton.originalColors')
            guids = set(d['guid'] for d in data)
            rhyton.Group.dissolve(guids)
            rhyton.ElementOverrides.clear(guids)
        elif not resetAll:
            breps = rhyton.GetBreps()
            rhyton.Group.dissolve(breps)
            rhyton.ElementOverrides.clear(breps)
    
    @staticmethod
    def export():
        breps = rhyton.GetBreps()
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