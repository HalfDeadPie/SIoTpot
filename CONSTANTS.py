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
PRIMARY_CONTROLLER = 1

NETWORKS = 'networks'
DECOYS = 'decoys'
CTX_HOME_ID = 'homeid'

SEQN_RANGE = 255

DEC_RECORD = 'records'
DEC_STATE = 'state'
DEC_STATE_OFF = '\x00'
DEC_STATE_ON = '\xff'
DEC_STATE_CONTROLLER = 'controller'

MONITOR = 'monitor'
GENERATOR = 'generator'
RECEIVER_CONN = 'receiver_conn'
TRANSMITTER_CONN = 'transmitter_conn'

CONFIG = 'config'
CONFIGURATION = 'configuration'

SENT_Q_SIZE = 10

LOGGER = 'iotpot_logger'

MESSAGE_BAD_CRC = 'Bad CRC'
MESSAGE_CRC_OK = 'CRC OK'
MESSAGE_RECORDS_MISSING = 'Decoys for this network are missing. Please, start recording them using a command "record"'
MESSAGE_VIRTUAL = '[VIRTUAL]'

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

Z_CMD_CLASS = 'cmd_class'
Z_CMD = 'cmd'

Z_SW_BINARY_TYPE = long(1)
Z_ACK_HEADER_TYPE = long(3)

Z_ACK_REQ_NO = long(1)
Z_ACK_REQ_YES = long(0)

CLASS_SWITCH_BINARY = 'SWITCH_BINARY'

CMD_SET = 'SET'
CMD_GET = 'GET'
CMD_REPORT = 'REPORT'
