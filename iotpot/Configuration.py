import sys

import configparser
from CONSTANTS import *


def parse(file):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file, encoding='utf8')
    return parser


class Configuration:
    def __init__(self, filepath, freq, samp, tx, records, networks, logging_file, alerts_file):
        self.home_id = None
        parser = parse(filepath)

        # COMMUNICATION PARAMETERS -------------------------------------------------------------------------------------

        self.freq = freq
        if not freq:
            try:
                self.freq = parser[COMMUNICATION][FREQ]
            except:
                self.freq = DEF_FREQ

        self.samp_rate = samp
        if not samp:
            try:
                self.samp_rate = parser[COMMUNICATION][SAMP_RATE]
            except:
                self.samp_rate = DEF_SAMP

        self.tx = tx
        if not tx:
            try:
                self.tx = parser[COMMUNICATION][TX_GAIN]
            except:
                self.tx = DEF_TX

        self.records_path = records
        if not records:
            try:
                self.records_path = parser[RECORDING][RECORDS_PATH]
            except:
                sys.exit(ERROR_MISSING_RECORD_PATH)

        self.networks_path = networks
        if not networks:
            try:
                self.networks_path = parser[NETWORKS][NETWORKS_PATH]
            except:
                sys.exit(ERROR_MISSING_NETWORK_PATH)

        self.logging_file = logging_file
        if not logging_file:
            try:
                self.logging_file = parser[LOGGING][LOGGING_PATH] + LOGGING_FILE
            except:
                sys.exit(ERROR_MISSING_LOGGING_PATH)

        self.alerts_file = logging_file
        if not alerts_file:
            try:
                self.alerts_file = parser[LOGGING][ALERTS_PATH] + ALERTS_FILE
            except:
                sys.exit(ERROR_MISSING_ALERTS_PATH)

        self.real_networks_name = REAL_NETWORKS_NAME
        self.virtual_networks_name = VIRTUAL_NETWORKS_NAME
