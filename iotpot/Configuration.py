import sys

import configparser
from CONSTANTS import *


def parse(file):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file, encoding='utf8')
    return parser


class Configuration():
    def __init__(self, filepath, freq, samp, tx, records, networks, logging_file, alerts_file):
        self.home_id = None
        parser = parse(filepath)

        # COMMUNICATION PARAMETERS -------------------------------------------------------------------------------------

        if parser.has_section(COMMUNICATION):
            parameters = parser[COMMUNICATION]

            # set frequency
            if not freq:
                try:
                    self.freq = parameters[FREQ]
                except:
                    self.freq = DEF_FREQ
            else:
                self.freq = freq

            if not samp:
                try:
                    self.samp_rate = parameters[SAMP_RATE]
                except:
                    self.samp_rate = DEF_SAMP
            else:
                self.samp_rate = samp

            if not tx:
                try:
                    self.tx = parameters[TX_GAIN]
                except:
                    self.tx = DEF_TX
            else:
                self.tx = tx




        if parser.has_section(RECORDING):
            parameters = parser[RECORDING]
            if not records:
                try:
                    self.records_path = parameters[RECORDS_PATH]
                except:
                    sys.exit(ERROR_MISSING_RECORD_PATH)
            else:
                self.records_path = records


        if parser.has_section(NETWORKS):
            parameters = parser[NETWORKS]
            if not networks:
                try:
                    self.networks_path = parameters[NETWORKS_PATH]
                except:
                    sys.exit(ERROR_MISSING_NETWORK_PATH)
            else:
                self.networks_path = networks




        if parser.has_section(LOGGING):
            parameters = parser[LOGGING]
            if not logging_file:
                try:
                    self.logging_file = parameters[LOGGING_PATH] + LOGGING_FILE
                except:
                    sys.exit(ERROR_MISSING_LOGGING_PATH)
            else:
                self.logging_file = logging_file

            if not alerts_file:
                try:
                    self.alerts_file = parameters[ALERTS_PATH] + ALERTS_FILE
                except:
                    sys.exit(ERROR_MISSING_ALERTS_PATH)
            else:
                self.alerts_file = logging_file

        self.real_networks_name = REAL_NETWORKS_NAME
        self.virtual_networks_name = VIRTUAL_NETWORKS_NAME
