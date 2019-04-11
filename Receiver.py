import time
import random
import array
from scapy.all import *
from CONSTANTS import ZWAVE, MESSAGE_BAD_CRC, NODE_ID_RANGE, FILE_TIME_FORMAT, RECORD_EXTENSION
from Support import *

import json

class Receiver():

    def __init__(self, monitor, configuration, network, decoys, logger):
        self.monitor = monitor
        self.configuration = configuration
        self.recorded_frames = {}
        self.networks = network
        self.decoys = decoys
        self.logger = logger
        self.free_ids = {}

    def filter_free_ids(self):
        for home_id, node_list in self.networks.iteritems():                  # for all real networks
            self.free_ids[home_id] = list(range(NODE_ID_RANGE))               # create range of free node IDs
            for node in node_list:                                            # and every real node
                self.free_ids[home_id].remove(node)                           # delete from free IDs

            if home_id in self.decoys.keys():                                 # and do same thing with decoys
                for node, _ in self.decoys[home_id].iteritems():
                    self.free_ids[home_id].remove(node)

    def list_decoys(self, home_id):
        try:
            return list(self.decoys[home_id].keys())
        except:
            return None

    def list_real_nodes(self, home_id):
        try:
            return list(self.networks[home_id])
        except:
            return None

    def calc_crc(self, frame):
        byte_array = array('B', str(frame[ZWaveReq]))
        try:
            byte_array.remove(frame.crc)
        except:
            self.logger.debug(MESSAGE_BAD_CRC)
            pass
        checksum = 0xff
        iterator = 0
        for byte in byte_array:
            checksum ^= byte
            # print("%d: %x" % (iterator, byte))
            iterator += 1

        return checksum

    def filter_frames(self, framelist):
        for frame in framelist:
            if ZWaveReq in frame:
                if ZWaveSwitchBin in frame:
                    command = readable_value(frame[ZWaveSwitchBin], 'cmd')
                    if command == "GET" or command == 'SET':
                        framelist.remove(frame)

    def save_networks(self):
        json.dump(self.networks,
                  open(self.configuration.networks_path + '/' +
                        self.configuration.real_networks_name, 'w'))
        json.dump(self.decoys,
                  open(self.configuration.networks_path + '/' +
                        self.configuration.virtual_networks_name, 'w'))

    def map_network(self, frame):
        home_id = text_id(frame.homeid)
        src, dst = frame.src, frame.dst
        safe_create_dict_list(self.networks, home_id)
        network = self.networks[home_id]

        # append new nodes if doesnt exists in networks
        safe_append(network, src)
        safe_append(network, dst)

    def virtualize_and_save_record(self, framelist, directory):
        mapped_pairs = {}
        record_name = str(time.strftime(FILE_TIME_FORMAT)) + RECORD_EXTENSION

        for home_id, nodelist in self.networks.iteritems():                          # for all saved real nodes
            for real_node in nodelist:
                virtual_node = random.choice(self.free_ids[home_id])                # generate random virtual ID
                self.free_ids[home_id].remove(virtual_node)                                  # remove it from free ID list
                mapped_pairs[real_node] = virtual_node                              # map virtual and real nodes

                # create dict with empty file list for record of decoy
                safe_create_dict_dict(self.decoys, home_id)                         # create decoys
                safe_create_dict_list(self.decoys[home_id], virtual_node)           # create their record list
                safe_append(self.decoys[home_id][virtual_node], record_name)        # remember decoy : [record list]

        for frame in framelist:                                                     # for all recorded frames
            frame.src = mapped_pairs[frame.src]                                     # swap real and virtual IDs
            frame.dst = mapped_pairs[frame.dst]                                     # ID of nodes

        wrpcap(directory + '/' + record_name, framelist)                            # save records to pcap files

    def delete_record(self, records):
        for record in records:
            os.remove(self.configuration.records_path + '/' + record)

    def remove_duplicate_decoys(self, frame):
        home_id = str(hex(frame.homeid))
        decoys = list(self.decoys[home_id].keys())
        src, dst = frame.src, frame.dst

        # if node id found in decoys, delete it and its records
        for node in src, dst:
            if node in decoys:
                records_to_delete = self.decoys[home_id][node]
                self.delete_record(records_to_delete)
                del (self.decoys[home_id][node])

    # start activity ---------------------------------------------------------------------------------------------------

    def start(self, recording):
        load_module('gnuradio')

        if recording:                                                               # in case of recording
            sniffradio(radio=ZWAVE, prn=lambda frame: self.record(frame))           # sniff frames until user signal

            for home_id, frame_list in self.recorded_frames.iteritems():            # for all recorded frames
                self.filter_frames(frame_list)                                      # filter GET and SET frames
                directory = self.configuration.records_path + '/' + home_id + '/'   # prepare directory for records
                safe_create_dir(directory)
                self.filter_free_ids()
                self.virtualize_and_save_record(frame_list, directory)              # virtualize and save them
        else:
            sniffradio(radio=ZWAVE, prn=lambda p: self.handle(p))

        self.save_networks()                                                        # always save networks and decoys

    # frame handlers ---------------------------------------------------------------------------------------------------

    def handle(self, frame):
        if self.calc_crc(frame) == frame.crc:
            decoys = self.list_decoys(text_id(frame.homeid))
            if frame.dst in decoys:
                self.monitor.analyse_frame(frame)

        else:
            self.logger.debug(MESSAGE_BAD_CRC)

    def record(self, frame):
        if self.calc_crc(frame) == frame.crc:
            frame.show()
            home_id = text_id(frame.homeid)

            # check if there is no ID duplicate in decoys
            if home_id in list(self.decoys.keys()):
                self.remove_duplicate_decoys(frame)

            self.map_network(frame)
            safe_create_dict_list(self.recorded_frames, home_id)
            self.recorded_frames[home_id].append(frame)
        else:
            self.logger.debug(MESSAGE_BAD_CRC)
