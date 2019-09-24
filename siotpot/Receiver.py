import collections
import sys
import threading

from scapy.all import *
from Support import *


class Receiver():

    def __init__(self, configuration, network, decoys, logger, frames_in, frames_out, responder=None):
        self.monitor = None
        self.configuration = configuration
        self.recorded_frames = {}
        self.networks = network
        self.decoys = decoys
        self.logger = logger
        self.free_ids = {}
        self.decoy_frames_in = frames_in
        self.decoy_frames_out = frames_out
        self.responder = responder
        load_module('gnuradio')

    def filter_free_ids(self):
        """
        prepare free NodeId of current network
        """
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
        """
        Provide list of decoys
        :param home_id: network identifier
        :return: list decoys
        """
        try:
            return list(self.decoys[home_id].keys())
        except:
            return None

    def list_real_nodes(self, home_id):
        """
        Provides list of real nodes
        :param home_id: network identifier
        :return: list devices
        """
        try:
            return list(self.networks[home_id])
        except:
            return None

    def save_networks(self):
        """
        Save decoy and network information to json
        """
        time.sleep(0.3)
        n_to_save = self.networks.copy()
        d_to_save = self.decoys.copy()

        if n_to_save:
            json.dump(n_to_save,
                      open(self.configuration.networks_path + '/' +
                           self.configuration.network_file, 'w'))

        if d_to_save:
            json.dump(d_to_save,
                      open(self.configuration.networks_path + '/' +
                           self.configuration.decoys_file, 'w'))

    def map_network(self, frame):
        """
        Learn NodeID from frame
        :param frame: Z-Wave frame
        """
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
        """
        Pop NodeID from list of free node identifiers
        :param home_id: network identifier
        :param real_node: identifier of mapped real device
        :return: int NodeId
        """
        if real_node == PRIMARY_CONTROLLER:
            return self.free_ids[home_id].pop(0)
        else:
            return self.free_ids[home_id].pop(10)

    def set_init_state(self, home_id, real_node, virtual_node):
        """
        Sets initial state of the decoy
        :param home_id: network identifier
        :param real_node: node identifier of real device
        :param virtual_node: node identifier of decoy
        """
        if str(real_node) == str(PRIMARY_CONTROLLER):
            self.decoys[home_id][virtual_node][DEC_STATE] = unicode(DEC_STATE_CONTROLLER)
        else:
            self.decoys[home_id][virtual_node][DEC_STATE] = unicode(DEC_STATE_OFF)

    def virtualize_and_save_record(self, frame_list, directory):
        """
        Anonymize records and save them
        (changes real NodeIDs to new identifiers)
        :param frame_list: list of received frames
        :param directory: directory where will be processed frames saved
        """
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
        """
        Delete saved records
        :param records: paths to records
        """
        for record in records:
            print 'removing:' + self.configuration.records_path + '/' + self.configuration.home_id + '/' + record
            os.remove(self.configuration.records_path + '/' + self.configuration.home_id + '/' + record)

    def remove_duplicate_decoys(self, frame):
        """
        Remove decoys if real device with same NodeID found. Removes records too
        :param frame: Frame including src and dst NodeId
        """
        home_id = str(hex(frame.homeid))
        decoys = list(self.decoys[home_id].keys())
        src, dst = frame.src, frame.dst

        # if node id found in decoys, delete it and its records
        for node in src, dst:
            if unicode(node) in decoys:
                records_to_delete = self.decoys[home_id][unicode(node)][DEC_RECORD]
                try:
                    self.delete_record(records_to_delete)
                except Exception as e:
                    print e
                try:
                    del (self.decoys[home_id][unicode(node)])
                except Exception as e:
                    print e

                self.decoys[home_id] = {key: val for key, val in self.decoys.items() if DEC_RECORD in records_to_delete}

    def decoy_in_frame(self, frame):
        """
        Check if a decoy NodeID is included in frame
        :param frame: Z-Wave frame
        :return: True/False
        """
        decoys = self.list_decoys(text_id(frame.homeid))
        if decoys and (str(frame.dst) in decoys or str(frame.src) in decoys):
            return True
        else:
            return False

    # start activity ---------------------------------------------------------------------------------------------------

    def start(self, recording, passive=False):
        """
        Main function of the receiver that start reception
        :param recording: Recording mode for recording real communication
        :param passive: Passive mode to monitor traffic
        """

        # if recording
        if recording:
            # use handler self.record
            sniffradio(radio=ZWAVE, prn=lambda frame: self.record(frame))  # sniff frames until user signal

            # for all recorded frames
            for home_id, frame_list in self.recorded_frames.iteritems():
                # prepare directory for records
                directory = self.configuration.records_path + '/' + home_id + '/'
                safe_create_dir(directory)
                self.filter_free_ids()
                # virtualize and save them
                self.virtualize_and_save_record(frame_list, directory)

        elif passive:
            # for passive monitoring use handle_passive
            sniffradio(radio=ZWAVE, prn=lambda p: self.handle_passive(p))
        else:
            # and for default mode of the honeypot, use handle function
            sniffradio(radio=ZWAVE, prn=lambda p: self.handle(p))

        # save potentialy updated information
        self.save_networks()  # always save networks and decoys

    def add_device(self, home_id):
        """
        Adds single device to specified network.
        :param home_id: network identifier
        """
        sniffradio(radio=ZWAVE, prn=lambda frame: self.new_device_handler(home_id, frame))

    # frame handlers ---------------------------------------------------------------------------------------------------

    def new_device_handler(self, home_id, frame):
        """
        Handler for adding a new device
        :param home_id: network identifier
        :param frame: received frame from real device
        """
        if ZWaveReq in frame:
            if calc_crc(frame) == frame.crc:
                if home_id == text_id(frame.homeid) or not home_id:
                    frame.show()
                    self.map_network(frame)
                    self.remove_duplicate_decoys(frame)
                    self.save_networks()

    def handle_passive(self, frame):
        """
        Handler for passive monitoring
        :param frame: received frame
        """
        if ZWaveReq in frame:
            # filter only specified network identifiers or receive all frame if not specified
            if not self.configuration.home_id or same_home_id(frame, self.configuration.home_id):
                # if verbose mode specified
                if self.configuration.verbose:
                    # show all received frames
                    frame.show()

                # if CRC is ok
                if calc_crc(frame) == frame.crc:
                    # and if its frame destined to decoy
                    if self.decoy_in_frame(frame):
                        # detect malicious frame
                        self.monitor.process_frame(STAT_MALICIOUS, frame, MESSAGE_MALICIOUS, MALTYPE_GENERAL)
                    else:
                        # else just process it and log information
                        self.monitor.process_frame(STAT_REAL, frame, MESSAGE_NETWORK)
                else:
                    # and if bad CRC, log information about that
                    self.monitor.process_frame(STAT_INVALID, frame, MESSAGE_BAD_CRC)

    def handle(self, frame):
        """
        Frame handler for default mode of the IoT honeypot
        :param frame: received frame
        """
        if ZWaveReq in frame:

            # compare specified network identifier HomeId
            if same_home_id(frame, self.configuration.home_id):

                # check CRC
                if calc_crc(frame) == frame.crc:

                    if self.decoy_in_frame(frame):
                        # decoy frame

                        frame_hash = calc_hash(frame)
                        self.monitor.process_frame(STAT_IN, frame, MESSAGE_VIRTUAL)

                        if frame_hash in self.decoy_frames_out:
                            # honeypot frame

                            if frame_hash not in self.decoy_frames_in:
                                # new frame
                                append_limited(self.decoy_frames_in, frame_hash, SENT_Q_SIZE)

                            else:
                                # duplicate frame
                                self.monitor.process_frame(STAT_MALICIOUS, frame, MESSAGE_MALICIOUS, MALTYPE_REPLAY)

                                if self.responder:
                                    self.responder.respond(frame)
                        else:
                            # foreign frame
                            self.monitor.process_frame(STAT_MALICIOUS, frame, MESSAGE_MALICIOUS, MALTYPE_FOREIGN)

                            if self.responder:
                                self.responder.respond(frame)
                    else:
                        # frame destined to real device
                        self.monitor.process_frame(STAT_REAL, frame, MESSAGE_NETWORK)
                else:
                    # invalid frame
                    self.monitor.process_frame(STAT_INVALID, frame, MESSAGE_BAD_CRC)
                    if self.responder and is_dst_decoy(frame, self.decoys):
                        self.responder.respond(frame)

    def record(self, frame):
        """
        Record mode handler
        :param frame: received frame
        """
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
