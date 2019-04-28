import sys

from scapy.all import *
from Support import *
from CONSTANTS import MESSAGE_RECORDS_MISSING


class Monitor:

    def __init__(self, configuration, network, decoys, logger, monitor_conn, receiver):
        self.configuration = configuration
        self.logger = logger
        self.network = network
        self.decoys = decoys
        self.conn = monitor_conn
        self.receiver = receiver

    def handle_generator(self, frame):
        self.logger.debug('Setting HomeID to configuration')
        home_id = text_id(frame.homeid)
        if home_id in self.decoys.keys():
            self.configuration.home_id = home_id

            try:
                self.conn.send(home_id)
            except:
                pass
        else:
            self.logger.error(MESSAGE_RECORDS_MISSING)
            sys.exit()

    def start(self, passive=False):
        self.receiver.start(False, passive)

    def record(self):
        self.receiver.start(recording=True)

    def detect_attempt_replay(self, frame):
        self.logger.warning('[REPLAY] ' + build_received_message(frame))

    def detect_attempt_modified(self, frame):
        self.logger.warning('[MODIFIED] ' + build_received_message(frame))

    def detect_invalid_frame(self, frame):
        if is_dst_decoy(frame, self.decoys):
            self.logger.debug('[INVALID] ' + build_received_message(frame))

    def log_device_message(self, frame):
        self.logger.debug(MESSAGE_NETWORK + ' ' + build_received_message(frame))

    def log_decoy_message(self, frame):
        self.logger.debug(MESSAGE_VIRTUAL + ' ' + build_received_message(frame))


