from config import ONE_HOP_TDD_CONFIG, TWO_HOP_TDD_CONFIG

# one hop test first
def virtual_subframe_capacity(device, interface, TDD_config):
	if device.link[interface]:
		status = device.link[interface][0].status
		real_subframe_count = len(list(filter(lambda x: x  if x is status else '', TDD_config)))
		VSC = {interface:device.capacity[interface]*real_subframe_count/len(TDD_config)}
		return VSC
	else:
		return {interface:None}