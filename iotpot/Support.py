import os
from array import array
from scapy.all import *
import xxhash
from CONSTANTS import *


def text_id(home_id):
    return str(hex(home_id))


def safe_create_dict_dict(dictionary, key):
    if not key in list(dictionary.keys()):
        dictionary[key] = {}


def safe_create_dict_list(dictionary, key):
    if not key in list(dictionary.keys()):
        dictionary[key] = []


def safe_append(list, node):
    if not node in list:
        list.append(node)


def safe_remove(list, node):
    if node in list:
        list.remove(node)


def safe_create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def readable_value(frame, key):
    human = lambda p, f: p.get_field(f).i2repr(p, getattr(p, f))
    return human(frame, key)


def calc_crc(frame):
    byte_array = array('B', str(frame[ZWaveReq]))
    try:
        byte_array.remove(frame.crc)
    except:
        pass
    checksum = 0xff
    iterator = 0
    for byte in byte_array:
        checksum ^= byte
        # print("%d: %x" % (iterator, byte))
        iterator += 1

    return checksum


def calc_hash(frame):
    temp_crc = frame.crc
    del (frame.crc)
    byte_array = array('B', str(frame[ZWaveReq]))
    frame.crc = temp_crc
    return xxhash.xxh32(byte_array).hexdigest()


def show_hex(frame):
    byte_array = array('B', str(frame[ZWaveReq]))
    for byte in byte_array:
        print("%x" % (byte)),
    print '\n'


def calc_length(frame):
    byte_array = array('B', str(frame[ZWaveReq]))
    return len(byte_array)


def build_received_message(frame):
    message = text_id(frame.homeid) + ' ' + \
              str(hex(frame.src)) + '->' + \
              str(hex(frame.dst)) + ' '

    try:
        command_class = readable_value(frame[ZWaveReq], Z_CMD_CLASS)
        message += str(command_class) + ' '
    except:
        pass

    try:
        command = readable_value(frame[ZWaveSwitchBin], Z_CMD)
        message += str(command) + ' '
    except:
        pass

    try:
        payload = readable_value(frame[Raw], 'load')
        message += str(payload)
    except:
        pass

    return message


def list_free_ids(taken):
    free_ids = set(list(range(NODE_ID_RANGE)))
    return list(filter(lambda x: x not in taken, free_ids))


def load_decoys_frames(path):
    files = []
    for root, dirs, files in os.walk(path):
        for filename in files:
            safe_append(files, filename)

    records = []
    for record_file in files:
        loaded_frames = rdpcap(path + '/' + record_file)
        for frame in loaded_frames:
            records.append(frame)

    return records
