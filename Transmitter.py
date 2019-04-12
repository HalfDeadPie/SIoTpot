from scapy.modules.gnuradio import *
from scapy.all import *
from scapy.layers.ZWave import *
from Support import *

class Transmitter():

    def __init__(self, configuration):
        self.configuration = configuration

    def send_frame(self, frame):
        crc = calc_crc(frame)
        frame.crc = crc
        send(frame, verbose=False)