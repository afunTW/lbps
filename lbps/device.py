# -*- coding: utf-8 -*-
#!/usr/bin/python
from Poisson import poisson

class Device:
	"""
		property:
		stream: point out the device is on upstream downstream by 'U' or 'D'
		buf: buffer size
	"""
	def __init__(self, stream, buf,  
