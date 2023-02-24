"""
Module for color operations.
"""
import colorsys
import os
import json
from collections import defaultdict
from rhyton.document import *
from rhyton.color import Color, ColorRange
from rhyton.ui import SelectionWindow


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
    def __init__(self):
        """
        Inits a new ColorScheme instance.
        """
        self.flag = 'rhyton.colorschemes'
        self.schemes = DocumentConfigStorage().get(
            self.flag, defaultdict())
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
    def toJSON(data, path):
        """
        Write color scheme to json

        Args:
            data (dict): The data to export
            path (str): The output file path.

        Returns:
            string: The json filepath
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
    def getFromUser(excludeSchemes=None):
        """
        Asks the user to select a rhyton color scheme.

        Args:
            excludeSchemes (string, optional): The name of one or more schemes to exclude. Defaults to None.

        Returns:
            dict: The selected rhyton color scheme
        """
        if not type(excludeSchemes) == list:
            excludeSchemes = [excludeSchemes]

        names = [scheme['name'] for scheme in ColorScheme().schemes
                         if not scheme['name'] in excludeSchemes]

        schemeName = SelectionWindow.show(sorted(names),
                message='Choose Color Scheme:')

        if not schemeName:
            return None

        return ColorScheme().schemes.get(schemeName)

    @staticmethod
    def apply(guids, schemeName):
        """
        Applies a rhyton color scheme to given objects.
        Updates the color scheme with new keys and colors.

        Args:
            guids (str): A list of Rhino objects ids
            schemeName (string): The name of the color scheme

        Returns:
            dict: Same return as ElementUserText but with key "color" added.
        """
        keys = ElementUserText.getKeys(guids)
        keyColors = ColorScheme().schemes.get(schemeName)
        if not keyColors:
            keyColors = ColorScheme().generate(keys)
            if not keyColors:
                return None
            ColorScheme().save(schemeName, keyColors)
        elif schemeName:
            ColorScheme().update(schemeName, keys)

        objectData = ElementUserText.get(guids, keys=schemeName)
        for entry in objectData:
            value = entry.get(schemeName)
            if value:
                entry['color'] = keyColors[value]

        ElementOverrides.apply(objectData)
        return objectData

    @staticmethod
    def applyGradient(guids, schemeName):
        """
        Applies a rhyton color gradient to given objects.

        Args:
            guids (str): A list of guids
            schemeName (_type_): _description_
        """
        values = ElementUserText.getValues(guids, fromKeys=schemeName).sort()
        keyColors = ColorScheme().generate(values, gradient=True)

        objectData = ElementUserText.get(guids, keys=schemeName)
        for entry in objectData:
            value = entry.get(schemeName)
            if value:
                entry['color'] = keyColors[value]

        ElementOverrides.apply(objectData)

    def generate(self, keys, excludeColors=None, gradient=False):
        """
        Generates a new color scheme.

        A color scheme has the following layout::

            current:
            {
                "name": <schemeName>,
                "data":{"key1": <hexcolor>}
            }

            proposed:
            {
                <schemeName>: {"key1": <hexcolor>}
            }

        Args:
            schemeName (string): The name of the color scheme
            keys (string): A set of keys
            excludeColors (string, optional): A list of colors to exclude
            gradient (int, optional): A tuple with start and end color

        Returns:
            dict: A color scheme
        """
        if not gradient:
            colors = ColorScheme().getColors(len(keys), excludeColors)
        elif gradient:
            colorsHSV = ColorRange(
                    len(keys), min=gradient[0], max=gradient[1]).getHSV()
            colors = []
            for hsv in colorsHSV:
                rgb = Color.HSVtoRGB(hsv)
                colors.append(Color.RGBtoHEX(rgb))

        keyColors = {}
        for value, color in zip(sorted(keys), colors):
            keyColors[value] = color

        return keyColors

    def update(self, schemeName, keys):
        """
        Updates a given color scheme with new keys and default colors
        and saves the changes to the DocumentConfigStorage.

        Args:
            scheme (dict): The color scheme to update
            keys (set): The keys to add

        Returns:
            dict: The updated color scheme
        """
        oldKeys = set(self.schemes[schemeName].keys())
        newKeys = list(set(keys).difference(oldKeys))

        if newKeys:
            excludeColors = self.schemes[schemeName].values()
            tempKeyColors = ColorScheme().generate(
                    newKeys, excludeColors=excludeColors)
            if not tempKeyColors:
                return None
            
            self.schemes[schemeName].update(tempKeyColors)

        DocumentConfigStorage().set(self.flag, self.schemes)

    def save(self, schemeName, keyValues):
        """
        Saves a single color scheme to the rhyton DocumentConfigStorage.

        Color schemes are stored as follows::

            {
                <schemeName1>: {"key1": "value1"},
                <schemeName2>: {"key1": "value1"}
            }

        Args:
            schemeName (str): The name of the color scheme
            keyValues (dict): The keys and colors associated with the name
        """
        scheme = {}
        scheme[schemeName] = keyValues
        self.schemes.update(scheme)
        DocumentConfigStorage().set(self.flag, self.schemes)

    def delete(self, schemeName):
        """
        Deletes a color scheme from the rhyton DocumenConfigStorage.

        Args:
            scheme (dict): A color scheme
        """
        if schemeName in self.schemes:
            del self.schemes[schemeName]
        
        DocumentConfigStorage().set(self.flag, self.schemes)

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
