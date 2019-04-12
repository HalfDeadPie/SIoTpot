import os
from array import array
from scapy.all import *

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
