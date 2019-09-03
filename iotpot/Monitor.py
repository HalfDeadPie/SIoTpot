import sys

from scapy.all import *
from Support import *
from CONSTANTS import MESSAGE_RECORDS_MISSING


class Monitor:

    def __init__(self, configuration, network, decoys, logger, stats):
        self.configuration = configuration
        self.logger = logger
        self.network = network
        self.decoys = decoys
        self.stats = stats

    def process_frame(self, group, frame, message, maltype=''):
        try:
            command = readable_value(frame[ZWaveSwitchBin], Z_CMD)
            self.stats[group][command] += 1

            if group is STAT_MALICIOUS:
                self.logger.warning(message + maltype + ' ' + build_received_message(frame))
            else:
                self.logger.debug(message + ' ' + build_received_message(frame))
        except IndexError as ind_ex:
            self.stats[group][STAT_ACK] += 1
        except KeyError as key_ex:
            self.stats[group][STAT_OTHER] += 1


            # template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            # message = template.format(type(e).__name__, e.args)




