# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'PEtab'
copyright = '2019, Daniel Weindl, Yannik Schälte, Dantong Wang, Carolin Loos, Jan Hasenauer, Paul Stapor, Elba Raimúndez Álvarez, Erika Dudkin, Charles Tapley Hoyt, Fabian Fröhlich'
author = 'Daniel Weindl, Yannik Schälte, Dantong Wang, Carolin Loos, Jan Hasenauer, Paul Stapor, Elba Raimúndez Álvarez, Erika Dudkin, Charles Tapley Hoyt, Fabian Fröhlich'

# The full version, including alpha/beta/rc tags
release = 'latest'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'recommonmark',
    'sphinx.ext.autosummary',
    'sphinx_markdown_tables',
    'nbsphinx'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

master_doc = 'index'

autosummary_generate = True

autodoc_default_options = {
    "members": None,
    "imported-members": ['petab'],
    "inherited-members": None,
    "private-members": None,
    "show-inheritance": None,
}

# For some reason causes sphinx import errors otherwise
autodoc_mock_imports = ['yaml']

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_context = {
    "display_github": True,
    "github_user": "ICB-DCM",
    "github_repo": "petab",
    "github_version": "develop",
    "conf_py_path": "/doc",
}

html_logo = 'logo/PEtab.png'
