from Receiver import Receiver
from scapy.all import *
from Support import *


class Monitor():

    def __init__(self, configuration, network, decoys, logger):
        self.configuration = configuration
        self.logger = logger
        self.network = network
        self.decoys = decoys
        self.receiver = Receiver(self, configuration, self.network, self.decoys, self.logger)

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
        if ZWaveReq in frame:
            if ZWaveSwitchBin in frame:
                command = readable_value(frame[ZWaveSwitchBin], 'cmd')
                if command == "GET" or command == 'SET':
                    self.logger.warning(self.build_attempt_message(frame))
