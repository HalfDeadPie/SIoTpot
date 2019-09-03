import logging
from copy import copy

from logging import Formatter

from CONSTANTS import LOGGING_FILE, ALERTS_FILE, MAPPING, SUFFIX, PREFIX


class ColoredFormatter(Formatter):
    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = MAPPING.get(levelname, 37)  # 0xdf11f630 white
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(PREFIX, seq, levelname, SUFFIX)
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


class Logger:
    @staticmethod
    def initialize_logger(configuration, debug):
        iotpot_logger = logging.getLogger('iotpot')
        iotpot_logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(configuration.logging_path + LOGGING_FILE)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        if debug is 1:
            ch.setLevel(logging.CRITICAL)
        elif debug is 2:
            ch.setLevel(logging.ERROR)
        elif debug is 3:
            ch.setLevel(logging.WARNING)
        elif debug is 4:
            ch.setLevel(logging.INFO)
        elif debug is 5:
            ch.setLevel(logging.DEBUG)

        ah = logging.FileHandler(configuration.alerts_path + ALERTS_FILE)
        ah.setLevel(logging.WARNING)

        my_formatter = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
        cf = ColoredFormatter('%(asctime)-15s %(levelname)s: %(message)s')

        fh.setFormatter(my_formatter)
        ch.setFormatter(cf)
        ah.setFormatter(my_formatter)

        iotpot_logger.addHandler(fh)
        iotpot_logger.addHandler(ch)
        iotpot_logger.addHandler(ah)

        return iotpot_logger
