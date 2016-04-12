# -*- coding: utf-8 -*-
#!/usr/bin/python3

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'description': 'simulation for LBPS',
	'author': 'chen-ming, yang',
	'url': 'https://github.com/endlessproof/lbps/tree/master',
	'author-email': 'endlessproof@gmail.com',
	'version': '0.1',
	'install_requires': ['nose'],
	'packages': ['lbps', 'math', 'numpy', 'scipy', 'matplotlib', 'hyrry.filesize'],
	'script': [],
	'name': 'lbps'
}

setup(**config);
