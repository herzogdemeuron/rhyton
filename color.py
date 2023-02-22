"""
Module for color operations.
"""
import rhyton
import colorsys
import os
import json
from collections import defaultdict
from rhyton.variables import RHYTON_COLORSCHEME
from rhyton.variables import DATA, IS_INSTANCE, NAME, PARAM_TYPE


class Color:
    """
    Class for basic color operations.
    """

    def __init__(self):
        """
        Inits a new Color instance.
        """
        pass
    
    @staticmethod
    def HSVtoRGB(hsv):
        """
        Convert a color from hsv to rgb.
        Args:
            hsv (tuple): A color in hsv format.
        Returns:
            tuple: A color in rgb format
        """
        return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2]))

    @staticmethod
    def RGBtoHEX(rgb):
        return '%02x%02x%02x' % rgb

    @staticmethod
    def HEXtoRGB(hex):
        """
        Converts a hex color string to rgb.
        Args:
            hex (sting): The hex color
        Returns:
            tuple: The rgb color
        """
        hex = hex.lstrip('#')
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))


class ColorScheme:
    """
    Class for handling relationships between labels and colors.
    """

    JSON_PATH = 'C:\\temp\\rhyton\\colorscheme.json'

    def __init__(self):
        """
        Inits a new ColorScheme instance.
        """
        self.COLOR_SCHEMES = 'rhyton.colorschemes'
        self.schemes = rhyton.ConfigStorage().get(
            self.COLOR_SCHEMES, defaultdict())
        self.defaultColors = [
                            '#F44336', '#E91E63', '#9C27B0', '#673AB7',
                            '#3F51B5', '#2196F3', '#03A9F4', '#00BCD4',
                            '#009688', '#4CAF50', '#8BC34A', '#CDDC39',
                            '#FFEB3B', '#FFC107', '#FF9800', '#FF5722',
                            '#795548', '#9E9E9E', '#607D8B'
                            ]
        self.additionalColors = [
                            '#D32F2F', '#C2185B', '#7B1FA2', '#512DA8',
                            '#303F9F', '#1976D2', '#0288D1', '#0097A7',
                            '#00796B', '#388E3C', '#689F38', '#AFB42B',
                            '#FBC02D', '#FFA000', '#F57C00', '#E64A19',
                            '#5D4037', '#616161', '#455A64'
                            ]
        self.extendedColors = self.defaultColors + self.additionalColors


    @staticmethod
    def toJSON(data, path=JSON_PATH):
        """
        Write color scheme to json
        Args:
            data (dict): The data to export
            path (str, optional): The output file path. Defaults to 'C:\temp\rhyton\colorscheme.json'.
        Returns:
            string: The json file
        """
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f:
            json.dump(data, f)

        return path

    @staticmethod
    def fromJSON(path):
        """
        Reads a color scheme from json.
        Args:
            path (string): The json file
        Returns:
            dict: The color scheme
        """
        with open(path, 'r') as f:
            scheme = json.load(f)

        return scheme

    @staticmethod
    def getFromUser(excludeSchemes=None, excludeViews=None):
        """
        Asks the user to select a rhyton color scheme.
        Args:
            excludeSchemes (string, optional): The name of one or more schemes to exclude. Defaults to None.
            excludeViews (string, optional): The id(s) of one ore more views to exclude. Defaults to None.
        Returns:
            dict: The selected rhyton color scheme
        """
        if not type(excludeSchemes) == list:
            excludeSchemes = [excludeSchemes]

        if excludeViews:
            if not type(excludeViews) == list:
                excludeViews = [excludeViews]

        schemes = []
        for scheme in ColorScheme().schemes:
            if not scheme[NAME] in excludeSchemes:
                schemes.append(scheme)

        names = [scheme[NAME] for scheme in schemes]

        if excludeViews:
            for scheme in schemes:
                for viewId in excludeViews:
                    try:
                        if not str(viewId) in rhyton.AffectedViews().get(scheme):
                            names.remove(scheme[NAME])
                    except:
                        names.remove(scheme[NAME])

        schemeName = forms.CommandSwitchWindow.show(sorted(names),
                message='Choose Color Scheme:')

        if not schemeName:
            return None

        return ColorScheme().load(schemeName)

    @staticmethod
    def apply(view, elements, schemeName, isInstance, type, patternId):
        """
        Applies a rhyton color scheme to given elements in given view.
        Updates the colors scheme with new keys and colors.
        Args:
            view (object): A Revit view
            elements (object): A list of Revit elements
            schemeName (string): The name of the color scheme
            isInstance (bool): True for instance parameters, false for type parameters
            type (string): The type of the parameter (Area, Number, Length, etc..)
            patternId (object): The Revit element id of the fillpattern to use
        Returns:
            dict: The applied and updated color scheme
        """
        keys = set()
        for element in elements:
            key = rhyton.GetKey(element, schemeName, isInstance, type)
            if key:
                keys.add(key)

        scheme = ColorScheme().load(schemeName)
        if not scheme:
            scheme = ColorScheme().generate(schemeName, keys, isInstance)
            if not scheme:
                return None
        elif scheme:
            ColorScheme().update(scheme, keys)

        ColorScheme().save(scheme)
        
        overriddenElements = rhyton.AffectedElements().get(
            scheme, viewId=view.Id)

        for element in elements:
            key = rhyton.GetKey(element, schemeName, isInstance, type)
            if key:
                colorHEX = scheme[DATA][key]
                colorRGB = rhyton.Color.HEXtoRGB(colorHEX)
                rhyton.ElementOverrides(view, element).set(colorRGB, patternId)
                overriddenElements.append(str(element.Id))
            else:
                rhyton.ElementOverrides(view, element).clear()
                try:
                    overriddenElements.remove(str(element.Id))
                except:
                    pass
        
        rhyton.AffectedElements().dump(scheme, view.Id, overriddenElements)  
        return scheme

    def generate(self, schemeName, keys,
            isInstance=None, paramType=None, excludeColors=None, gradient=False):
        """
        Generates a new color scheme.
        Args:
            schemeName (string): The name of the color scheme
            keys (string): A set of keys
            excludeColors (string, optional): A list of colors to exclude
            gradient (int, optional): A tuple with start and end color
        Returns:
            dict: A color scheme: {name: schemeName, data: {key: color}}
        """
        if not gradient:
            colors = ColorScheme().getColors(len(keys), excludeColors)
        elif gradient:
            colorsHSV = ColorRange(len(keys), min=gradient[0], max=gradient[1]).getHSV()
            colors = []
            for hsv in colorsHSV:
                rgb = Color.HSVtoRGB(hsv)
                colors.append(Color.RGBtoHEX(rgb))
        scheme = {}
        scheme[NAME] = schemeName
        scheme[IS_INSTANCE] = isInstance
        scheme[PARAM_TYPE] = paramType
        scheme[DATA] = {}
        for value, color in zip(sorted(keys), colors):
            scheme[DATA][value] = color
        return scheme

    def update(self, colorScheme, keys):
        """
        Updates a given color scheme with new keys and default colors.
        Args:
            colorScheme (dict): The color scheme to update
            keys (set): The keys to add
        Returns:
            dict: The updated color scheme
        """
        newkeys = set()
        for key in keys:
            if key not in colorScheme[DATA].keys():
                newkeys.add(key)

        if newkeys:
            excludeColors = colorScheme[DATA].values()
            tempScheme = ColorScheme().generate(
                'tempName', newkeys, excludeColors=excludeColors)
            if not tempScheme:
                return None
            colorScheme[DATA].update(tempScheme[DATA])

        return colorScheme

    def load(self, schemeName):
        """
        Loads a color scheme by name.
        Args:
            schemeName (string): The name of the color scheme
        Returns:
            dict: The color scheme
        """
        for scheme in self.schemes:
            if scheme[NAME] == schemeName:
                return scheme
        return None

    def save(self, scheme):
        """
        Saves a color scheme to the revitron DocumentConfigStorage.
        Args:
            scheme (dict): A color scheme
        """
        writeSchemes = []
        update = False
        for existingScheme in self.schemes:
            if scheme[NAME] == existingScheme[NAME]:
                existingScheme[DATA] = scheme[DATA]
                update = True
            writeSchemes.append(existingScheme)
        
        if not update:
            writeSchemes.append(scheme)
        rhyton.ConfigStorage().set(self.COLOR_SCHEMES, writeSchemes)

    def delete(self, scheme):
        """
        Deletes a color scheme from the revitron DocumenConfigStorage.
        Args:
            scheme (dict): A color scheme
        """
        usedSchemes = []
        for docScheme in self.schemes:
            if not docScheme[NAME] == scheme[NAME]:
                usedSchemes.append(docScheme)
        
        rhyton.ConfigStorage().set(self.COLOR_SCHEMES, usedSchemes)

    def getColors(self, count, excludeColors=[]):
        """
        Gets a given amount of colors.
        Args:
            count (int): The number of colors to get
            excludeColors (string, optional): List of colors to exclude. Defaults to None.
        Returns:
            string: A list of colors
        """
        import random

        def filterColors(excludeColors, colors):
            if excludeColors:
                availableColors = filter(
                    lambda color: color not in excludeColors, colors)
                return availableColors
            else:
                 return colors

        self.defaultColors = filterColors(excludeColors, self.defaultColors)
        self.extendedColors = filterColors(excludeColors, self.extendedColors)

        if count <= len(self.defaultColors):
            availableColors = self.defaultColors
        elif count <= len(self.extendedColors):
            availableColors = self.extendedColors
        elif count >= len(self.extendedColors) and count < 100:
            hsvColors = ColorRange(count).getHSV()
            availableColors = []
            for hsvColor in hsvColors:
                rgbColor = Color.HSVtoRGB(hsvColor)
                hexColor = Color.RGBtoHEX(rgbColor)
                availableColors.append(hexColor)
        else:
            print('Too many keys, colors are indistiguishable.')
            return None

        colors = random.sample(availableColors, count)
        return colors
