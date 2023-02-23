"""
Module for interacting with the user.
Provides ready-made functions that can be used by buttons in any extension.
"""
import rhinoscriptsyntax as rs
from utils import GetBreps
from document import ElementUserText

class Visualization:

    @staticmethod
    def byGroup():
        # breps = GetBreps()
        # keys = set(i for i in ElementUserText.get(breps))
        # keys.remove('guid')
        # keys.add("grand_total")
        # get key from user
        # apply color scheme to objects
        pass

    @staticmethod
    def byValue():
        # breps = GetBreps()
        # make gradient
        pass

    @staticmethod
    def reset():
        # selected objects or 
        # all visualizations
        pass
    
    @staticmethod
    def export():
        pass


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
    def toCSV():
        # get data
        # get file path
        # rhyton.CSV.write(file, data)
        pass

    @staticmethod
    def toJSON():
        # get data
        # get file
        # rhyton.JSON.write(file, data)
        pass


class SelectionWindow:

    @staticmethod
    def show(options, message=None):
        if not type(options) == dict:
            options = {(i, i) for i in options}

        res = rs.ListBox(options.keys(), message)
        if res:
            return options[res]