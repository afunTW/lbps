from . import device

class BaseStation(device.OneHopDevice):
    count = 0

    def __init__(self, name=None):
        super(BaseStation, self).__init__()
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(self.__class__.count)]
            )
        )
