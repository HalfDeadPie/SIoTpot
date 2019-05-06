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
        self.stats = {STAT_REAL: 0, STAT_DECOY: 0, STAT_MALICIOUS: 0, STAT_INVALID: 0,
                      STAT_SET: 0, STAT_GET: 0, STAT_REPORT: 0, STAT_OTHER: 0,
                      STAT_INVALID_GET: 0, STAT_INVALID_SET:0, STAT_INVALID_REPORT: 0}

    def start(self, passive=False):
        self.receiver.start(False, passive)

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

    def inc_set(self, invalid=False):
        if invalid:
            self.stats[STAT_INVALID_SET] += 1
        else:
            self.stats[STAT_SET] += 1
            self.stats[STAT_MALICIOUS] += 1

    def inc_get(self, invalid=False):
        if invalid:
            self.stats[STAT_INVALID_GET] += 1
        else:
            self.stats[STAT_GET] += 1
            self.stats[STAT_MALICIOUS] += 1

    def inc_report(self, invalid=False):
        if invalid:
            self.stats[STAT_INVALID_REPORT] += 1
        else:
            self.stats[STAT_REPORT] += 1
            self.stats[STAT_MALICIOUS] += 1

    def inc_invalid(self):
        self.stats[STAT_INVALID] += 1

    def inc_real(self):
        self.stats[STAT_REAL] += 1

    def inc_other(self):
        self.stats[STAT_OTHER] += 1
        self.stats[STAT_MALICIOUS] += 1

    def record(self):
        self.receiver.start(recording=True)

    def detect_malicious(self, frame):
        try:
            command = readable_value(frame[ZWaveSwitchBin], Z_CMD)
            if command == CMD_SET:
                self.inc_set()
                self.logger.warning(MESSAGE_MALICIOUS + ' ' + build_received_message(frame))
            elif command == CMD_GET:
                self.inc_get()
                self.logger.warning(MESSAGE_MALICIOUS + ' ' + build_received_message(frame))
            elif command == CMD_REPORT:
                self.inc_report()
                self.logger.warning(MESSAGE_MALICIOUS + ' ' + build_received_message(frame))
        except:
            pass

    def detect_invalid_frame(self, frame):
        self.stats[STAT_INVALID] += 1
        self.process_invalid_frame(frame)
        self.logger.debug(MESSAGE_BAD_CRC + ' ' + build_received_message(frame))

    def process_invalid_frame(self, frame):
        if is_dst_decoy(frame, self.decoys):
            try:
                command = readable_value(frame[ZWaveSwitchBin], Z_CMD)
                if command == CMD_SET:
                    self.inc_set(True)
                elif command == CMD_GET:
                    self.inc_get(True)
                elif command == CMD_REPORT:
                    self.inc_report(True)
            except:
                pass


    def log_device_message(self, frame):
        self.stats[STAT_REAL] += 1
        self.logger.debug(MESSAGE_NETWORK + ' ' + build_received_message(frame))

    def log_decoy_message(self, frame):
        self.stats[STAT_DECOY] += 1
        self.logger.debug(MESSAGE_VIRTUAL + ' ' + build_received_message(frame))
