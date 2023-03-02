"""
rhyton is a base package that you can develop your data-centric 
Rhino extensions ontop of.

These are the main topics that rhtyon covers:

    - Object User Text
    - Document User Text
    - Object Color 'Overrides' / Data Visualization
    - Exporting Object User Text

Since rhyton is a data focussed package, it handles Rhino objects internally as
dictionaries::

    {"guid": <guid>,"'key1": <value1>, "key2", <value2>}

To be more efficient, most functions also take a list of guid's that 
share the same keys and values::

    {"guid": [<guid1>, <guid2>],"'key1": <value1>, "key2", <value2>}

The ''Rhyton'' class is used as a common base class to share information
across the package.

Coding Style Guid:

    - 'camelCase' function and variable names.
    - Title 'CamelCase' class names.
    - Class names and functions are designed for reading flow:
        * rhyton.Visualize('extension_name').byGroup()
        * rhyton.Export('extension_name').toCSV()
    - "" for text that is presented to the user.
    - '' for internal stings.
    - Functions in ui.py should not take arguments to keep out clutter.
    - The Rhyton('extension_name') class instance is meant to be the 
    only **configurable** point of entry.
    - **All** modules, classes and function must have extensive docstrings
    - Keep in-line comments to a minimum.
"""
# rhyton imports
from rhyton.ui import *
from rhyton.color import *
from rhyton.document import *
from rhyton.export import *
from rhyton.utils import *