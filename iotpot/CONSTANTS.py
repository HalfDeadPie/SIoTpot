COMMUNICATION = 'communication'

RECORDING = 'recording'
RECORDS_PATH = 'records_path'

NETWORKS = 'networks'
REC_NETWORK_FILE = 'network.json'
REC_DECOYS_FILE = 'decoys.json'

FREQ = 'freq'
SAMP_RATE = 'sample_rate'
TX_GAIN = 'tx_gain'
ZWAVE = 'Zwave'
PRIMARY_CONTROLLER = 1

NETWORKS = 'networks'
NETWORKS_PATH = 'networks_path'
DECOYS = 'decoys'
CTX_HOME_ID = 'homeid'

LOGGING = 'logging'

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

MESSAGE_CRC_OK = 'CRC OK'
MESSAGE_RECORDS_MISSING = 'Decoys for this network are missing. Please, start recording them using a command "record"'
MESSAGE_VIRTUAL = '[VIRTUAL]'
MESSAGE_NETWORK = '[NETWORK]'
MESSAGE_BAD_CRC = '[INVALID]'
MESSAGE_MALICIOUS = '[MALICOUS]'
MESSAGE_STARTING_GENERATOR = 'Starting the traffic generator'

NODE_ID_RANGE = 232

FILE_TIME_FORMAT = "%Y%m%d-%H%M%S"
RECORD_EXTENSION = '.pcap'

MAPPING = {
    'DEBUG': 37,  # white
    'INFO': 36,  # cyan
    'WARNING': 33,  # yellow
    'ERROR': 31,  # red
    'CRITICAL': 41,  # white on red bg
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

FILE_LOGS = 'iotpot.log'
FILE_ALERTS = 'alerts.log'

INFO_NEW_REAL = 'New device has been found: '

WARNING_NO_REAL = 'WARNING! Mapping of real network is missing. Colision of decoys and real' \
                  'devices can disrup real network. It is suggested to record or map real network.'

ERROR_MISSING_NETWORK = 'Missing mapping of network!'
ERROR_MISSING_RECORD_PATH = 'Missing path to records! Please, use the configuration file or the option'
ERROR_MISSING_NETWORK_PATH = 'Missing path to networks! Please, use the configuration file or the option'
ERROR_MISSING_LOGGING_PATH = 'Missing path for a logging file! Please, use the configuration file or the option'
ERROR_MISSING_ALERTS_PATH = 'Missing path for a alerts file! Please, use the configuration file or the option'
ERROR_NO_GENERATED_TRAFFIC = 'Missing records for '
ERROR_NO_HOMEID_TO = 'Missing target network!'
ERROR_WRONG_TESTING = 'Missing command for test (SET/GET/REPORT)!'
ERROR_MISSING_DECOYS = 'Missing decoys for this network! It is recommened to record real network first.'

EXIT_TRAFFIC_GENERATOR = 'TERMINATING TRANSMITTING PROCESS'
EXIT_RECEIVER_GENERATOR = 'TERMINATING RECEIVING PROCESS'

EXIT = 'exit'


LOGGING_PATH = 'logging_path'
ALERTS_PATH = 'alerts_path'
LOGGING_FILE = 'iotpot.log'
ALERTS_FILE = 'alerts.log'

DEF_SAMP = 2000000
DEF_FREQ = 868420000
DEF_TX = 25

DEFAULT_DATA_PATH = 'data/'
DEFAULT_NETWORKS_PATH = DEFAULT_DATA_PATH + 'networks'
DEFAULT_RECORDS_PATH = DEFAULT_DATA_PATH + 'records/'
DEFAULT_HOME_ID = '0xdf11f630'

# statistic constant keys
STAT_REAL = 'real'
STAT_OUT = 'out'
STAT_IN = 'in'
STAT_MALICIOUS = 'malicious'
STAT_INVALID = 'invalid'

STAT_GET = CMD_GET
STAT_SET = CMD_SET
STAT_REPORT = CMD_REPORT
STAT_ACK = 'ACK'
STAT_OTHER = 'OTHER'
STAT_CMDS = (STAT_GET, STAT_SET, STAT_REPORT, STAT_ACK, STAT_OTHER)

RESPOND_SLEEP_TIME = 0.3

FRAMES_IN = 'in'
FRAMES_OUT = 'out'

MALTYPE_REPLAY = '[REPLAY]'
MALTYPE_FOREIGN = '[FOREIGN]'

DEBUG_LEVEL = 'debug'
