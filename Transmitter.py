from scapy.modules.gnuradio import *
from scapy.all import *
from scapy.layers.ZWave import *
from Support import *

class Transmitter():

    def __init__(self, configuration, transmitter_conn):
        self.configuration = configuration
        self.conn = transmitter_conn

    def send_frame(self, frame):
        crc = calc_crc(frame)
        frame.crc = crc
        self.conn.send(calc_hash(frame))
        send(frame, verbose=False)