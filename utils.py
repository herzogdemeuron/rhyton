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

def GetBreps(filterByTypes=[1073741824, 16, 8]):
    """
    Gets the currently selected Rhino objects or asks the user to go get some.
    
    Allowed objects are by default::

        8 = Surface
        16 = Polysurface
        1073741824 = Extrusion

    Returns:
        list: A list of Rhino objects ids.
    """
    breps = rs.GetObjects(filter=filterByTypes, preselect=True)
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
    mergedDict = {}
    
    for d in data:
        values = tuple(d[key] for key in keys)
        
        if values not in mergedDict:
            mergedDict[values] = {"guid": []}
        
        mergedDict[values]["guid"].append(d["guid"])
        
    return [{"guid": v["guid"], **dict(zip(keys, k))} for k, v in mergedDict.items()]