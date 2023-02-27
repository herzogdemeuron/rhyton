"""
Module for general utily functions.
"""
import rhinoscriptsyntax as rs

def Key(key):
    """
    Sanitize given key to meet rhyton standards.

    Args:
        key (str): The key to clean.

    Returns:
        str: The sanitized key.
    """
    return key.replace(' ', "_").lower()

def Value(value):
    """
    Sanitize given value to meet rhyton standards.

    Args:
        value (str): The value to clean.

    Returns:
        str: The sanitized value.
    """
    return str(value).replace('_', " ").title()

def GetBreps(filterByTypes=[8, 16, 1073741824]):
    """
    Gets the currently selected Rhino objects or asks the user to go get some.
    
    Allowed objects are by default::

        8 = Surface
        16 = Polysurface
        8192 = Text Dot
        1073741824 = Extrusion

    Returns:
        list: A list of Rhino objects ids.
    """
    selection = rs.GetObjects(preselect=True, select=True)
    if not selection:
        return None
    
    breps = [str(b) for b in selection if rs.ObjectType(b) in filterByTypes]
    return breps

def toList(data):
    """
    Ensures that the input data is a list.

    Args:
        data (mixed): The object to check

    Returns:
        list: The original object or the object wrapped in a list.
    """
    if isinstance(data, list):
        return data
    else:
        return [data]
    
def groupGuidsBy(data, keys):
    """
    Re-organizes a list of dictionaies by given key.
    All dicts in the list that share the same values for given keys will be
    merged into one dict.
    All the "guid"s of the source dicts get stored as a list under the 
    "guid" key in the merged dict and the source dicts are removed from the list.
    All keys other than the input keys will be removed in the process to
    prevent ambiguity.

    Args:
        data (dict): The Dictionary to re-organize.
        keys (list[str]): The list of keys to group by.
    """
    mergedDict = dict()
    
    for d in data:
        values = tuple(d[key] for key in keys)
        
        if values not in mergedDict:
            mergedDict[values] = {"guid": []}
        
        mergedDict[values]["guid"].append(d["guid"])
        
    result = []
    for k, v in mergedDict.items():
        newDict = dict(zip(keys, k))
        newDict["guid"] = v["guid"]
        result.append(newDict)

    return result

def formatNumber(number):
    """
    Formats a number.

    Args:
        number (float): The number to format.

    Returns:
        float: The formatted number.
    """
    return number