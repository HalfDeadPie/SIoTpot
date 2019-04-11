COMMUNICATION = 'communication'

RECORDING = 'recording'
RECORDS_PATH = 'records_path'

NETWORKS_PATH = 'networks'
REAL_NETWORKS_NAME = 'real_networks.json'
VIRTUAL_NETWORKS_NAME = 'virtual_networks.json'

FREQ = 'frequency'
SAMP_RATE = 'sample_rate'
TX_GAIN = 'tx_gain'
ZWAVE = 'Zwave'


MONITOR = 'monitor'

CONFIG = 'config'

CRC_BYTE = 10

LOGGER = 'iotpot_logger'

MESSAGE_BAD_CRC = 'Bad CRC'
MESSAGE_CRC_OK = 'CRC OK'

NODE_ID_RANGE = 232

FILE_TIME_FORMAT = "%Y%m%d-%H%M%S"
RECORD_EXTENSION = '.pcap'


MAPPING = {
    'DEBUG'   : 37, # white
    'INFO'    : 36, # cyan
    'WARNING' : 33, # yellow
    'ERROR'   : 31, # red
    'CRITICAL': 41, # white on red bg
}

PREFIX = '\033['
SUFFIX = '\033[0m'
