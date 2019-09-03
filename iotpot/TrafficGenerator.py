import sys

from scapy.layers.ZWave import *
from Support import *
from CONSTANTS import *


class TrafficGenerator:

    def __init__(self, configuration, networks, decoys, logger, stats, transmitter):
        self.configuration = configuration
        self.networks = networks
        self.decoys = decoys
        self.logger = logger
        self.decoy_frame_lists = {}
        self.records = []
        self.transmitter = transmitter
        self.stats = stats

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

    def start(self, test=None):
        home_id = None
        if self.configuration.home_id:
            home_id = self.configuration.home_id
            self.logger.debug('Setting HomeID for traffic generator: ' + home_id)

        self.load_decoys_frames(home_id)

        time.sleep(5)
        self.logger.info(MESSAGE_STARTING_GENERATOR)
        while True:
            for frame in self.records:
                self.transmitter.send_frame(frame)
