from scapy.layers.ZWave import *

from Transmitter import Transmitter


class TrafficGenerator():

    def __init__(self, configuration):
        self.configuration = configuration
        self.transmitter = Transmitter(configuration)

    def start(self):
        # homeid = int('0xdf11f630', 16)
        # nodeid = 2
        # basic = ZWave(homeid=homeid, dst=nodeid) / ZWaveBasic(cmd="GET")
        # self.transmitter.send_frame(basic)
        frames = rdpcap("pcap-file.pcap")

