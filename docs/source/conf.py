# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import datetime
import revitron_sphinx_theme

path1 =  os.path.abspath('../../..')
path2 =  os.path.abspath('../..')
print(path1)
print(path2)
sys.path.insert(0, path1)
# path2 = os.path.join(os.path.dirname(__file__), '../../lib')
# print(path2)
sys.path.append(path2)

project = 'Rhyton'
copyright = '2023, Herzog & de Meuron'
author = 'Herzog & de Meuron'
release = '0.1'

master_doc = 'index'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
]

autodoc_mock_imports = ['rhinoscriptsyntax', 'Rhino']

add_module_names = False

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

templates_path = ['_templates']
exclude_patterns = ['modules.rst']

ogp_site_url = "https://rhyton.readthedocs.io/"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'revitron_sphinx_theme'
html_theme_options = {
    'navigation_depth': 5,
    'github_url': 'https://github.com/herzogdemeuron/rhyton',
    'color_scheme': 'dark'
}

html_logo = '_static/rhyton.svg'
html_title = 'Rhyton'
html_favicon = '_static/favicon.ico'

html_context = {
    'landing_page': {
        'menu': [{
            'title': 'Rhyton',
            'url': 'https://rhyton.readthedocs.io/'
        }, {
            'title': 'Developer Guide',
            'url': 'rhyton.html'
        }, {
            'title': 'HdM-DT',
            'url': 'https://www.herzogdemeuron.com/topics/design-technologies/'
        }]
    }
}

html_sidebars = {}

# html_logo = '_static/rhyton.svg'
# html_title = 'Rhyton'

html_static_path = ['_static']
html_css_files = ['custom.css']

html_js_files = []