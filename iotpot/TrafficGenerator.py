import sys

from scapy.layers.ZWave import *
from Support import *
from CONSTANTS import *


class TrafficGenerator():

    def __init__(self, configuration, networks, decoys, logger, generator_conn, transmitter):
        self.configuration = configuration
        self.conn = generator_conn
        self.networks = networks
        self.decoys = decoys
        self.logger = logger
        self.decoy_frame_lists = {}
        self.records = []
        self.transmitter = transmitter

    def load_decoys_frames(self, home_id):
        record_files = []

        for node in list(self.decoys[home_id].keys()):
            record_files.append(self.decoys[home_id][node][DEC_RECORD])

        unique_records = reduce(lambda l, x: l.append(x) or l if x not in l else l, record_files, [])

        if len(unique_records) == 0:
            self.transmitter.send_exit()
            time.sleep(0.3)
            self.logger.error(ERROR_NO_GENERATED_TRAFFIC + home_id)
            self.logger.info(EXIT_TRAFFIC_GENERATOR)
            sys.exit()

        for record_file in unique_records:
            loaded_frames = rdpcap(self.configuration.records_path + '/' + home_id + '/' + record_file[0])
            for frame in loaded_frames:
                self.records.append(frame)

    def is_set(self, frame):
        try:
            if ZWaveSwitchBin in frame:
                cmd = readable_value(frame[ZWaveSwitchBin], Z_CMD)

                if cmd == CMD_SET:
                    return True
                else:
                    return False

        except Exception as e:
            pass

    def start(self, test=None):
        if self.configuration.home_id:
            home_id = self.configuration.home_id
        else:
            home_id = self.conn.recv()
        self.logger.debug('Setting HomeID for traffic generator: ' + home_id)

        if test == CMD_SET:
            self.records = rdpcap('/home/halfdeadpie/PycharmProjects/IoT-Honeypot/tests/records/set_frames.pcap')
        elif test == CMD_GET:
            self.records = rdpcap('/home/halfdeadpie/PycharmProjects/IoT-Honeypot/tests/records/get_frames.pcap')
        elif test == CMD_REPORT:
            self.records = rdpcap('/home/halfdeadpie/PycharmProjects/IoT-Honeypot/tests/records/report_frames.pcap')
        else:
            self.load_decoys_frames(home_id)

        time.sleep(5)
        self.logger.info(MESSAGE_STARTING_GENERATOR)
        if test:
            counter = 1
            for frame in self.records:
                if counter % 5 == 0:
                    self.transmitter.send_test_frame(frame, False)
                else:
                    self.transmitter.send_test_frame(frame, True)
                time.sleep(1)
                counter += 1
            self.logger.info('TEST FINISHED!')
        else:
            while True:
                for frame in self.records:
                    self.transmitter.send_frame(frame)
                    time.sleep(1)
