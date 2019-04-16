import sys

from Receiver import Receiver
from scapy.all import *
from Support import *
from CONSTANTS import MESSAGE_RECORDS_MISSING


class Monitor():

    def __init__(self, configuration, network, decoys, logger, monitor_conn, receiver_conn):
        self.configuration = configuration
        self.logger = logger
        self.network = network
        self.decoys = decoys
        self.conn = monitor_conn
        self.receiver = Receiver(self, configuration, self.network, self.decoys, self.logger, receiver_conn)

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

    def start(self):
        self.receiver.start(False)

    def record(self):
        self.receiver.start(True)

    def build_attempt_message(self, frame):
        message = text_id(frame.homeid) + ' ' + \
                  str(frame.src) + '->' + \
                  str(frame.dst) + ' '

        try:
            command_class = readable_value(frame[ZWaveReq], 'cmd_class')
            message += str(command_class) + ' '
        except:
            pass


        try:
            command = readable_value(frame[ZWaveSwitchBin], 'cmd')
            message += str(command) + ' '
        except:
            pass


        try:
            payload = readable_value(frame[Raw], 'load')
            message += str(payload)
        except:
            pass

        return message

    def analyse_frame(self, frame):
        #self.logger.debug(self.build_attempt_message(frame))
        if ZWaveReq in frame:
            if ZWaveSwitchBin in frame:
                command = readable_value(frame[ZWaveSwitchBin], 'cmd')
                if command == "GET" or command == 'SET':
                    self.logger.warning(self.build_attempt_message(frame))

    def detect_attempt_replay(self, frame):
        self.logger.warning('[REPLAY] ' + self.build_attempt_message(frame))

    def detect_attempt_modified(self, frame):
        self.logger.warning('[MODIFIED] ' + self.build_attempt_message(frame))

