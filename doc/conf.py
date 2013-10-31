import os.path
import sys

# Allow autodoc to find the carmen package.
sys.path.insert(0, os.path.abspath('..'))

project = 'Carmen'
release = '0.0.3'
copyright = '2013, Roger Que and Mark Dredze'

master_doc = 'index'
exclude_patterns = ['_build']

extensions = ['sphinx.ext.autodoc']

# HTML output options.
html_domain_indices = False
html_use_index = False
