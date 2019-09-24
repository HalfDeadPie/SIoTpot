import sys

import configparser
from CONSTANTS import *


def parse(file):
    """
    Parses configuration INI file
    :param file: INI file
    :return: parsed file
    """
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file, encoding='utf8')
    return parser


class Configuration:
    def __init__(self, filepath, freq, samp, tx, records, networks, logging_path, alerts_path):
        self.home_id = None
        parser = parse(filepath)

        # frequency
        self.freq = freq
        if not freq:
            try:
                self.freq = parser[COMMUNICATION][FREQ]
            except:
                self.freq = DEF_FREQ

        # sample rate
        self.samp_rate = samp
        if not samp:
            try:
                self.samp_rate = parser[COMMUNICATION][SAMP_RATE]
            except:
                self.samp_rate = DEF_SAMP

        # TX gain
        self.tx = tx
        if not tx:
            try:
                self.tx = parser[COMMUNICATION][TX_GAIN]
            except:
                self.tx = DEF_TX

        # path of records
        self.records_path = records
        if not records:
            try:
                self.records_path = parser[RECORDING][RECORDS_PATH]
            except:
                sys.exit(ERROR_MISSING_RECORD_PATH)

        # path of network information
        self.networks_path = networks
        if not networks:
            try:
                self.networks_path = parser[NETWORKS][NETWORKS_PATH]
            except:
                sys.exit(ERROR_MISSING_NETWORK_PATH)

        # path of logging file
        self.logging_path = logging_path
        if not logging_path:
            try:
                self.logging_path = parser[LOGGING][LOGGING_PATH]
            except:
                sys.exit(ERROR_MISSING_LOGGING_PATH)

        # path to alerts file
        self.alerts_path = alerts_path
        if not alerts_path:
            try:
                self.alerts_path = parser[LOGGING][ALERTS_PATH]
            except:
                sys.exit(ERROR_MISSING_ALERTS_PATH)


        self.network_file = REC_NETWORK_FILE
        self.decoys_file = REC_DECOYS_FILE

        self.verbose = False

    def paths(self):
        """
        return path of records, network information, logging file and alerts file
        :return: String records, String network_info, String logging_file, String alerts_file
        """
        return [self.records_path, self.networks_path, self.logging_path, self.alerts_path]

    def path_network_file(self):
        return self.networks_path + '/' + self.network_file

    def path_decoys_file(self):
        return self.networks_path + '/' + self.decoys_file

