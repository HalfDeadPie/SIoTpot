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
            # to read command in frame
            command = readable_value(frame[ZWaveSwitchBin], Z_CMD)

            # increment command's counter
            self.stats[group][command] += 1

            # if its malicious frame
            if group is STAT_MALICIOUS:
                # log warning
                self.logger.warning(message + maltype + ' ' + build_received_message(frame))
            else:
                # just log a frame
                self.logger.debug(message + ' ' + build_received_message(frame))
        except IndexError as ind_ex:
            # in case of missing command, It is ACK
            self.stats[group][STAT_ACK] += 1
        except KeyError as key_ex:
            # any other commands
            self.stats[group][STAT_OTHER] += 1
        # except Exception as e:
        #     template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        #     message = template.format(type(e).__name__, e.args)
        #     print message




