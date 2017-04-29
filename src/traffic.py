class Traffic(object):
    # lambd(ms)
    def __init__(self,
        name='traffic',
        bitrate=0,
        packet_size=0,
        delay_budget=0,
        lambd=0
    ):
        self.name = name
        self.__bitrate = bitrate
        self.__packet_size = packet_size
        self.__delay_budget = delay_budget
        self.__lambd = lambd

    @property
    def bitrate(self): return self.__bitrate
    @property
    def packet_size(self): return self.__packet_size
    @property
    def delay_budget(self): return self.__delay_budget
    @property
    def lambd(self): return self.__lambd

class VoIP(Traffic):
    def __init__(self,
        name='VoIP',
        bitrate=10,
        packet_size=800,
        delay_budget=50,
        lambd=10/1000):
        super(VoIP, self).__init__(
            name=name,
            bitrate=bitrate,
            packet_size=packet_size,
            delay_budget=delay_budget,
            lambd=lambd
        )

class Video(Traffic):
    def __init__(self,
        name='Video',
        bitrate=250,
        packet_size=8000,
        delay_budget=300,
        lambd=250/1000):
        super(Video, self).__init__(
            name=name,
            bitrate=bitrate,
            packet_size=packet_size,
            delay_budget=delay_budget,
            lambd=lambd
        )

class OnlineVideo(Traffic):
    def __init__(self,
        name='OnlineVideo',
        bitrate=10,
        packet_size=800,
        delay_budget=300,
        lambd=10/1000):
        super(OnlineVideo, self).__init__(
            name=name,
            bitrate=bitrate,
            packet_size=packet_size,
            delay_budget=delay_budget,
            lambd=lambd
        )