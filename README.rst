SIoTpot
***************************
IoT honeypot
============================
This project is the implementation of my Master's Thesis. SIoTpot is the IoT honeypot
for the Z-Wave protocol.

- records legitimate communication in order to create system of decoys
- transmit simulated communication to lure attackers
- passive monitoring of a network

Abstract of the Thesis
==========================

The goals of this thesis lay among theoretical analysis of the Internet of Things (IoT) concept and its security issues, and practical research and development of a new unique device called 'IoT honeypot'.
The analytical part of the thesis summarizes existing hardware and software solutions and concentrates on Software Defined Radio
(SDR) technology, which was used for the development of IoT honeypot.
The developed prototype currently supports a wide-spread Z-Wave protocol.
However, the design is universal enough to support other IoT protocols in the future.
The motivation of this thesis was to create a device that can collect information about IoT traffic, detect potential attackers, and act as a decoy that complicates attackers to discover and hack real deployed IoT devices, such as sensors, switches, and so on.
The result of the thesis is a working IoT honeypot that supports multiple modes of operation (such as passive or interactive mode) and that can be deployed as a part of a Z-Wave infrastructure. It is as a complement to other security tools and mechanisms that increase the security of IoT infrastructure.

Install
==================

**RTL-SDR dongle**

RTL-SDR dongle is used for reception of Z-Wave frames. It is necessary to install drivers for this device. The installation guide which can be found in https://www.rtl-sdr.com/rtl-sdr-quick-start-guide/.

**HackRF One**

HackRF One is used for transmission of Z-Wave frames. Installation guide for this device can be found in https://github.com/mossmann/hackrf/wiki/Operating-System-Tips.

**EZ-Wave**

Scapy-radio ensures digital signal processing and frame parsing. EZ-Wave offers examples of usage of Scapy-radio functions. Since EZ-Wave includes Scapy-radio too, Scapy-radio can be installed according to manual in https://github.com/cureHsu/EZ-Wave.

**GNU Radio Companion**

GNU Radio Companion can be used for GRC block modification. Installation guide for GNU Radio Companion can be found in https://wiki.gnuradio.org/index.php/InstallingGR.

**Replacement of GRC blocks**

It is highly recommended to replace files in:


    $HOME/.scapy/radio/Zwave/Zwave.grc
    $HOME/.scapy/radio/Zwave/top_block.py

with files *Zwave.grc* and *top_block.py* that can be found in this repository.

**SIoTpot**

Clone this repository:

    git clone https://github.com/HalfDeadPie/SIoTpot

and use *setup.py* for installation:

    python setup.py install

Examples of Usage
====================

All subcommands and options can be displayed using :

    siotpot --help

It is highly recommended to use a configuration file. An example of configuration file can be found in this repository (*config.cfg*):

    [communication]
    sample_rate = 2000000
    freq = 868420000
    tx_gain = 25

    [recording]
    records_path = /home/[USER]/Desktop/iotpot_data/records

    [networks]
    networks_path = /home/[USER]/Desktop/iotpot_data/networks

    [logging]
    logging_path = /home/[USER]/Desktop/iotpot_data/
    alerts_path = /home/[USER]/Desktop/iotpot_data/

Recording starts with:

    siotpot record

The main functionality starts with:

    siotpot run HOME-ID

All persisent information of the IoT honeypot can be displayed using this subcommand:

    siotpot status

Passive monitoring

    siotpot listen

All persistent information of the IoT honeypot can be deleted using this subcommand:

    siotpot reset

Testing
====================

The IoT honeypot uses RTL-SDR dongle for receiving and HackRF One for transmitting. Both devices use an antenna.
All testing is done using a single transmitter.
The prototype of the IoT honeypot is the Python package that is installed on a notebook.
The notebook has four CPU cores, 6\,GB of RAM memory and the 64-bit operating system Ubuntu 16.04 LTS.
The IoT honeypot has records of decoys that are prepared to operate in a real Z-Wave network

Testing results reveals the IoT honeypot is able to receive aproximately 50% of Z-Wave frames sent by the Scapy-radio and HackRF one.

**It is not recommended to use this tool as only protection of Z-Wave networks!**