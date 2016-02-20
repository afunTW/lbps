# -*- coding: utf-8 -*-                                                                                                                       
#!/usr/bin/python3

import os, sys, inspect

currFolder = os.path.realpath( os.path.abspath( os.path.split( inspect.getfile( inspect.currentframe()))[0]))

if currFolder not in sys.path:
	sys.path.insert(0, currFolder);

parentFolder = os.path.realpath(os.path.split(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))[0]);

if parentFolder not in sys.path:
	sys.path.insert(0, parentFolder);

