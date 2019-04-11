import configparser
from CONSTANTS import COMMUNICATION, TX_GAIN, FREQ, SAMP_RATE, RECORDING, RECORDS_PATH, \
    NETWORKS_PATH, REAL_NETWORKS_NAME, VIRTUAL_NETWORKS_NAME

def parse(file):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file, encoding='utf8')
    return parser

class Configuration():
    def __init__(self, filepath):
        parser = parse(filepath)
        if parser.has_section(COMMUNICATION):
            parameters = parser[COMMUNICATION]
            self.freq = parameters[FREQ]
            self.samp_rate = parameters[SAMP_RATE]
            self.tx = parameters[TX_GAIN]

        if parser.has_section(RECORDING):
            parameters = parser[RECORDING]
            self.records_path = parameters[RECORDS_PATH]

        self.networks_path = NETWORKS_PATH
        self.real_networks_name = REAL_NETWORKS_NAME
        self.virtual_networks_name = VIRTUAL_NETWORKS_NAME