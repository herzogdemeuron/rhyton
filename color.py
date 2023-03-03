"""
Module for color operations.
"""
# python standard imports
import os
import json
import random
import colorsys
from itertools import repeat
from collections import defaultdict

# rhyton imports
from main import Rhyton
from ui import SelectionWindow
from document import DocumentConfigStorage, ElementUserText, ElementOverrides

class Color:
    """
    Class for basic color operations.
    """
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
        """
        Convert an RGB color to HEX.

        Args:
            rgb (tuple): The RGB color.

        Returns:
            str: The HEX color
        """
        return '%02x%02x%02x' % rgb

    @staticmethod
    def HEXtoRGB(hexColor):
        """
        Converts a hex color string to rgb.

        Args:
            hexColor (sting): The hex color

        Returns:
            tuple: The rgb color
        """
        hexColor = hexColor.lstrip('#')
        return tuple(int(hexColor[i:i+2], 16) for i in (0, 2, 4))


class ColorScheme(Rhyton):
    """
    Class for handling relationships between labels and colors.
    """
    def __init__(self):
        """
        Inits a new ColorScheme instance.
        """
        self.flag = Rhyton.EXTENSION_COLOR_SCHEMES
        self.schemes = DocumentConfigStorage().get(
            self.flag, defaultdict())
        self.defaultColors = [
                            '#F44336', '#E91E63', '#9C27B0', '#673AB7',
                            '#3F51B5', '#2196F3', '#03A9F4', '#00BCD4',
                            '#009688', '#4CAF50', '#8BC34A', '#CDDC39',
                            '#FFEB3B', '#FFC107', '#FF9800', '#FF5722',
                            '#795548', '#607D8B'
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

    @classmethod
    def getFromUser(cls, excludeSchemes=None):
        """
        Asks the user to select a rhyton color scheme.

        Args:
            excludeSchemes (string, optional): The name of one or more schemes to exclude. Defaults to None.

        Returns:
            dict: The selected rhyton color scheme
        """
        if not type(excludeSchemes) == list:
            excludeSchemes = [excludeSchemes]

        names = [scheme[cls.NAME] for scheme in ColorScheme().schemes
                         if not scheme[cls.NAME] in excludeSchemes]
        schemeName = SelectionWindow.show(sorted(names),
                message='Choose Color Scheme:')
        if not schemeName:
            return None

        return ColorScheme().schemes.get(schemeName)

    @classmethod
    def apply(cls, guids, schemeName):
        """
        Applies a rhyton color scheme to given objects.
        Updates the color scheme with new keys and colors.

        Args:
            guids (str): A list of Rhino objects ids
            schemeName (string): The name of the color scheme

        Returns:
            dict: Same return as ElementUserText but with key "color" added.
        """
        keys = ElementUserText.getValues(guids, keys=schemeName)
        keyColors = ColorScheme().schemes.get(schemeName)
        if not keyColors:
            keyColors = ColorScheme().generate(keys)
            if not keyColors:
                return None
            ColorScheme().save(schemeName, keyColors)
        else:
            ColorScheme().update(schemeName, keys)
            keyColors = ColorScheme().schemes.get(schemeName)

        objectData = ElementUserText.get(guids, keys=schemeName)
        for entry in objectData:
            value = entry.get(schemeName)
            if value:
                entry[cls.COLOR] = keyColors[value]
            else:
                entry[cls.COLOR] = cls.HEX_WHITE
                entry[schemeName] = cls.NOT_AVAILABLE

        ElementOverrides.apply(objectData)
        return objectData

    @classmethod
    def applyGradient(cls, guids, schemeName, gradient):
        """
        Applies a rhyton color gradient to given objects.

        Args:
            guids (str): A list of guids.
            schemeName (str): The name of the color scheme.
            gradient (list): Two RGB colors: [start, end]
        """
        rawValues = ElementUserText.getValues(guids, keys=schemeName)
        values = sorted(rawValues)
        keyColors = ColorScheme().generate(values, gradient=gradient)
        objectData = ElementUserText.get(guids, keys=schemeName)
        for entry in objectData:
            value = entry.get(schemeName)
            if value:
                entry[cls.COLOR] = keyColors[value]

        ElementOverrides.apply(objectData)
        return objectData

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
            colorsRGB = Gradient.betweenRgbColors(len(keys), gradient[0], gradient[1])
            colors = [Color.RGBtoHEX(rgb) for rgb in colorsRGB]

        keyColors = dict()
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

        DocumentConfigStorage().save(self.flag, self.schemes)

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
        scheme = dict()
        scheme[schemeName] = keyValues
        self.schemes.update(scheme)
        DocumentConfigStorage().save(self.flag, self.schemes)

    def delete(self, schemeName):
        """
        Deletes a color scheme from the rhyton DocumenConfigStorage.

        Args:
            scheme (dict): A color scheme
        """
        if schemeName in self.schemes:
            del self.schemes[schemeName]
        
        DocumentConfigStorage().save(self.flag, self.schemes)

    def getColors(self, count, excludeColors=[]):
        """
        Gets a given amount of colors.
        Args:
            count (int): The number of colors to get
            excludeColors (string, optional): List of colors to exclude. Defaults to None.
        Returns:
            string: A list of colors
        """
        self.defaultColors = self._filterColors(
                excludeColors, self.defaultColors)
        
        self.extendedColors = self._filterColors(
                excludeColors, self.extendedColors)
        
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
    
    def _filterColors(self, excludeColors, colors):
        if excludeColors:
            availableColors = filter(
                lambda color: color not in excludeColors, colors)
            return availableColors
        else:
            return colors


class ColorRange:
    """
    Class for working with color ranges.
    """
    def __init__(self, count, min=0, max=100):
        """
        Inits a new ColorRange instance.

        Accepted values::

            0 <= min < 100
            1 < max <= 100
            count < max - min
        """
        if 0 <= min and min < 100:
            self.min = min
        else:
            return None
        
        if 1 < max and max <= 100:
            self.max = max
        else:
            return None
            
        if count < max - min:
            self.count = count
        else:
            return None

        self.range = max - min

        if not self.count <= self.range:
            print('Count bigger than range.')
            return None

    def getHSV(self):
        """
        Gets a list of colors in hsv format.

        Returns:
            list: A list of hsv colors
        """
        hsv = []
        for i in [
                x * 0.01 for x in range(
                        self.min, 
                        self.max,
                        (self.range / self.count))]:
            hsv.append((i, 0.5, 0.9))
        return hsv


class Gradient:

    @classmethod
    def betweenRgbColors(cls, count, start, end):
        """
        Create a range of colors by interpolating the individual r, g, b values.

        Args:
            count (int): The total amout of colors to return.
            start (tuple): The start color.
            end (tuple): The end color.
        """
        rangeR = cls._getRange(start[0], end[0], count)
        rangeG = cls._getRange(start[1], end[1], count)
        rangeB = cls._getRange(start[2], end[2], count)
        return tuple(zip(rangeR, rangeG, rangeB))

    @staticmethod
    def _getRange(start, end, count):
        if start == end:
            return repeat(start, count)

        step = (end - start) / count
        increments = []
        for i in range(count):
            increments.append(int(start))
            start += step

        return increments