import time

from scapy.layers.ZWave import *

from Transmitter import Transmitter


class TrafficGenerator():

    def __init__(self, configuration, networks, decoys, logger, generator_conn, transmitter_conn):
        self.configuration = configuration
        self.conn = generator_conn
        self.networks = networks
        self.decoys = decoys
        self.logger = logger
        self.decoy_frame_lists = {}
        self.records = []
        self.transmitter = Transmitter(configuration, transmitter_conn)

    def load_decoys_frames(self, home_id):
        record_files = self.decoys[home_id].values()
        unique_records = reduce(lambda l, x: l.append(x) or l if x not in l else l, record_files, [])
        for record_file in unique_records[0]:
            loaded_frames = rdpcap(self.configuration.records_path + '/' + home_id + '/' + record_file)
            for frame in loaded_frames:
                self.records.append(frame)


    def start(self):
        # receive HomeID of virtual network from receiver
        home_id = self.conn.recv()
        self.logger.debug('Setting HomeID for traffic generator: ' + home_id)
        self.load_decoys_frames(home_id)
        while True:
            for frame in self.records:
                self.transmitter.send_frame(frame)
                time.sleep(2)

