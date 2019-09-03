import random

from scapy.modules.gnuradio import *
from scapy.all import *
from scapy.layers.ZWave import *
from Support import *
from CONSTANTS import *


class Transmitter:

    def __init__(self, configuration, frames_out, stats):
        self.configuration = configuration
        self.seqn = long(random.randint(0, SEQN_RANGE))
        self.frames_out = frames_out
        self.stats = stats

    def send_frame(self, frame):
        self.seqn += 1
        if self.seqn >= SEQN_RANGE:
            self.seqn = 0
        frame.seqn = self.seqn
        frame[ZWaveReq].crc = calc_crc(frame)
        append_limited(self.frames_out, calc_hash(frame), SENT_Q_SIZE)
        time.sleep(0.1)

        try:
            command = readable_value(frame[ZWaveSwitchBin], Z_CMD)
            self.stats[STAT_OUT][command] += 1

        except IndexError as ind_ex:
            self.stats[STAT_OUT][STAT_ACK] += 1
        except KeyError as key_ex:
            self.stats[STAT_OUT][STAT_OTHER] += 1

        send(frame, verbose=False)
