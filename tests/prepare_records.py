from scapy.all import *
from iotpot.Support import  *

load_module('gnuradio')

record = rdpcap('/home/halfdeadpie/PycharmProjects/IoT-Honeypot/iotpot_data/records/0xdf11f630/20190428-141924.pcap')

for r in record:
    try:
        if readable_value(r[ZWaveSwitchBin], 'cmd') == 'REPORT':
            set_frame = r.copy()
    except:
        pass

attack_frames = []
for i in range (1, 101):
    new_frame = set_frame.copy()
    new_frame.seqn = long(i)
    new_frame[ZWaveReq].crc = calc_crc(new_frame)
    attack_frames.append(new_frame)

wrpcap("/home/halfdeadpie/PycharmProjects/IoT-Honeypot/tests/records/report_frames.pcap", attack_frames)


