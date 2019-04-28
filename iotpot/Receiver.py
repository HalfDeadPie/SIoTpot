import collections
import sys
import threading
import time
import random
import json

from scapy.all import *
from Support import *


class Receiver():

    def __init__(self, configuration, network, decoys, logger, receiver_conn, responder):
        self.monitor = None
        self.configuration = configuration
        self.recorded_frames = {}
        self.networks = network
        self.decoys = decoys
        self.logger = logger
        self.free_ids = {}
        self.conn = receiver_conn
        self.decoy_frames_out = collections.deque(SENT_Q_SIZE * [None], SENT_Q_SIZE)
        self.decoy_frames_in = collections.deque(SENT_Q_SIZE * [None], SENT_Q_SIZE)
        self.responder = responder
        load_module('gnuradio')

    def filter_free_ids(self):
        for home_id, node_list in self.networks.iteritems():  # for all real networks
            self.free_ids[home_id] = list(range(1, NODE_ID_RANGE))  # create range of free node IDs
            self.free_ids[home_id] = map(str, self.free_ids[home_id])
            for node in node_list:  # and every real node
                self.free_ids[home_id].remove(str(node))  # delete from free IDs

            if home_id in self.decoys.keys():  # and do same thing with decoys
                for node, _ in self.decoys[home_id].iteritems():
                    try:
                        self.free_ids[home_id].remove(node)
                    except:
                        pass

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

    def save_networks(self):
        time.sleep(0.3)
        n_to_save = self.networks.copy()
        d_to_save = self.decoys.copy()

        if n_to_save:
            json.dump(n_to_save,
                      open(self.configuration.networks_path + '/' +
                           self.configuration.real_networks_name, 'w'))
        if d_to_save:
            json.dump(d_to_save,
                      open(self.configuration.networks_path + '/' +
                           self.configuration.virtual_networks_name, 'w'))

    def map_network(self, frame):
        home_id = text_id(frame.homeid)
        src, dst = frame.src, frame.dst
        safe_create_dict_list(self.networks, home_id)
        network = self.networks[home_id]

        if src not in self.networks[home_id]:
            self.logger.info(INFO_NEW_REAL + str(src))
            safe_append(network, src)

        # append new nodes if doesnt exists in networks
        if dst not in self.networks[home_id]:
            self.logger.info(INFO_NEW_REAL + str(dst))
            safe_append(network, dst)

    def choose_id(self, home_id, real_node):
        if real_node == PRIMARY_CONTROLLER:
            return self.free_ids[home_id].pop(0)
        else:
            return self.free_ids[home_id].pop(10)

    def set_init_state(self, home_id, real_node, virtual_node):
        if str(real_node) == str(PRIMARY_CONTROLLER):
            self.decoys[home_id][virtual_node][DEC_STATE] = unicode(DEC_STATE_CONTROLLER)
        else:
            self.decoys[home_id][virtual_node][DEC_STATE] = unicode(DEC_STATE_OFF)

    def virtualize_and_save_record(self, frame_list, directory):
        mapped_pairs = {}
        record_name = str(time.strftime(FILE_TIME_FORMAT)) + RECORD_EXTENSION

        for home_id, nodelist in self.networks.iteritems():
            for real_node in nodelist:
                virtual_node = self.choose_id(home_id, real_node)
                mapped_pairs[real_node] = virtual_node  # map virtual and real nodes
                safe_create_dict_dict(self.decoys, home_id)
                safe_create_dict_dict(self.decoys[home_id], virtual_node)
                safe_create_dict_list(self.decoys[home_id][virtual_node], DEC_RECORD)
                safe_append(self.decoys[home_id][virtual_node][DEC_RECORD], record_name)
                self.set_init_state(home_id, real_node, virtual_node)

        swap_mapping(frame_list, mapped_pairs)
        wrpcap(directory + '/' + record_name, frame_list)  # save records to pcap files

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
                records_to_delete = self.decoys[home_id][node][DEC_RECORD]
                self.delete_record(records_to_delete)
                del (self.decoys[home_id][node])

    def synchronizer(self):
        while True:
            if self.conn.poll():
                frame_hash = self.conn.recv()
                if frame_hash == EXIT:
                    self.logger.info(EXIT_RECEIVER_GENERATOR)
                    sys.exit()
                self.decoy_frames_out.appendleft(frame_hash)
            else:
                pass

    def decoy_in_frame(self, frame):
        decoys = self.list_decoys(text_id(frame.homeid))
        if decoys and (str(frame.dst) in decoys or str(frame.src) in decoys):
            return True
        else:
            return False

    # start activity ---------------------------------------------------------------------------------------------------

    def start(self, recording, passive=False):

        if recording:  # in case of recording
            sniffradio(radio=ZWAVE, prn=lambda frame: self.record(frame))  # sniff frames until user signal

            for home_id, frame_list in self.recorded_frames.iteritems():  # for all recorded frames
                directory = self.configuration.records_path + '/' + home_id + '/'  # prepare directory for records
                safe_create_dir(directory)
                self.filter_free_ids()
                self.virtualize_and_save_record(frame_list, directory)  # virtualize and save them
        elif passive:
            sniffradio(radio=ZWAVE, prn=lambda p: self.handle_passive(p))
        else:
            sync_thread = threading.Thread(name='synch_thread', target=self.synchronizer)
            sync_thread.setDaemon(True)
            sync_thread.start()
            sniffradio(radio=ZWAVE, prn=lambda p: self.handle(p))

        self.save_networks()  # always save networks and decoys

    def add_device(self, home_id):
        sniffradio(radio=ZWAVE, prn=lambda frame: self.new_device_handler(home_id, frame))

    # frame handlers ---------------------------------------------------------------------------------------------------

    def new_device_handler(self, home_id, frame):
        if ZWaveReq in frame:
            if calc_crc(frame) == frame.crc:
                if home_id == text_id(frame.homeid) or not home_id:
                    frame.show()
                    self.map_network(frame)
                    self.remove_duplicate_decoys(frame)
                    self.save_networks()

    def handle_passive(self, frame):
        if ZWaveReq in frame:
            if calc_crc(frame) == frame.crc:
                frame.show()
                # self.map_network(frame)
            else:
                self.logger.debug(MESSAGE_BAD_CRC)

    def handle(self, frame):
        if ZWaveReq in frame:
            if same_home_id(frame, self.configuration.home_id):
                if calc_crc(frame) == frame.crc:

                    # only first message to stick on Home ID
                    if not self.configuration.home_id:
                        self.monitor.handle_generator(frame)

                    # decoy frame
                    if self.decoy_in_frame(frame):
                        self.monitor.log_decoy_message(frame)
                        frame_hash = calc_hash(frame)

                        # if sent by honeypot
                        if frame_hash in self.decoy_frames_out:

                            # if not received yet
                            if frame_hash not in self.decoy_frames_in:
                                self.decoy_frames_in.appendleft(frame)

                            # if received duplicate
                            else:
                                self.monitor.detect_attempt_replay(frame)
                                if self.responder:
                                    self.responder.respond(frame)

                        # if was not sent by honeypot
                        else:
                            self.monitor.detect_attempt_modified(frame)
                            if self.responder:
                                self.responder.respond(frame)
                    else:
                        self.monitor.log_device_message(frame)
                else:
                    self.monitor.detect_invalid_frame(frame)
                    if self.responder and is_dst_decoy(frame, self.decoys):
                        self.responder.respond(frame)

    def record(self, frame):
        if ZWaveReq in frame:
            if calc_crc(frame) == frame.crc:
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
