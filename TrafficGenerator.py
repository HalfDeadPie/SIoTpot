import time

from scapy.layers.ZWave import *

from Transmitter import Transmitter


class TrafficGenerator():

    def __init__(self, configuration, networks, decoys, logger):
        self.configuration = configuration
        self.transmitter = Transmitter(configuration)
        self.networks = networks
        self.decoys = decoys
        self.logger = logger
        self.decoy_frame_lists = {}
        self.records = []

    def load_decoys_frames(self, home_id):
        record_files = self.decoys[home_id].values()
        unique_records = reduce(lambda l, x: l.append(x) or l if x not in l else l, record_files, [])
        for record_file in unique_records[0]:
            loaded_frames = rdpcap(self.configuration.records_path + '/' + home_id + '/' + record_file)
            for frame in loaded_frames:
                self.records.append(frame)


    def start(self, home_id):
        self.load_decoys_frames(home_id)
        while True:
            for frame in self.records:
                self.transmitter.send_frame(frame)
                time.sleep(2)

