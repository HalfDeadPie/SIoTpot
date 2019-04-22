import configparser
from CONSTANTS import COMMUNICATION, TX_GAIN, FREQ, SAMP_RATE, RECORDING, RECORDS_PATH, \
    NETWORKS_PATH, REAL_NETWORKS_NAME, VIRTUAL_NETWORKS_NAME


def parse(file):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file, encoding='utf8')
    return parser


class Configuration():
    def __init__(self, filepath, freq, samp, tx, records):
        self.home_id = None
        parser = parse(filepath)
        if parser.has_section(COMMUNICATION):
            parameters = parser[COMMUNICATION]

            # set frequency
            if not freq:
                self.freq = parameters[FREQ]
            else:
                self.freq = freq

            if not samp:
                self.samp_rate = parameters[SAMP_RATE]
            else:
                self.samp_rate = samp

            if not tx:
                self.tx = parameters[TX_GAIN]
            else:
                self.tx = tx

        if parser.has_section(RECORDING):
            parameters = parser[RECORDING]
            if not records:
                self.records_path = parameters[RECORDS_PATH]
            else:
                self.records_path = records

        self.networks_path = NETWORKS_PATH
        self.real_networks_name = REAL_NETWORKS_NAME
        self.virtual_networks_name = VIRTUAL_NETWORKS_NAME
