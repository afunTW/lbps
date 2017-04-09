from . import device

class RelayNode(device.TwoHopDevice):
    count = 0

    def __init__(self, name=None):
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(self.__class__.count)]
            )
        )
        super(RelayNode, self).__init__(name=self.name)
