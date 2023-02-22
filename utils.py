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

def GetBreps():
    breps = rs.GetObjects(filter=[1073741824, 16, 8], preselect=True)
    return breps