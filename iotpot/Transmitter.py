import random

from scapy.modules.gnuradio import *
from scapy.all import *
from scapy.layers.ZWave import *
from Support import *
from CONSTANTS import *

class Transmitter():

    def __init__(self, configuration, transmitter_conn):
        self.configuration = configuration
        self.conn = transmitter_conn
        self.seqn = long(random.randint(0, SEQN_RANGE))

    def send_frame(self, frame):
        self.seqn += 1
        if self.seqn >= SEQN_RANGE:
            self.seqn = 0
        frame.seqn = self.seqn

        frame[ZWaveReq].crc = calc_crc(frame)

        if not self.conn.send(calc_hash(frame)):
            self.conn.send(calc_hash(frame))
        send(frame, verbose=False)

    def send_test_frame(self, frame, hash):
        self.seqn += 1
        if self.seqn >= SEQN_RANGE:
            self.seqn = 0
        frame.seqn = self.seqn

        frame[ZWaveReq].crc = calc_crc(frame)

        if hash:
            self.conn.send(calc_hash(frame))

        send(frame, verbose=False)

    def send_exit(self):
        self.conn.send(EXIT)