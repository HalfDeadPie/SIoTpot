from scapy.modules.gnuradio import *
from scapy.all import *
from scapy.layers.ZWave import *
import time

class Transmitter():

    def __init__(self, configuration):
        self.configuration = configuration

    def send_frame(self, frame):
        send(frame, verbose=False)