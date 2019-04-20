import json
import multiprocessing
import os
import time

from scapy.all import *

import click
import logging

from Configuration import Configuration
from Monitor import Monitor
from Receiver import Receiver
from Responder import Responder
from TrafficGenerator import TrafficGenerator
from CONSTANTS import *

from Support import readable_value, show_hex
from copy import copy
from logging import Formatter

from multiprocessing import Process, Pipe

from Transmitter import Transmitter


def load_json(file):
    if os.path.isfile(file):
        return json.load(open(file))
    else:
        return {}


class ColoredFormatter(Formatter):

    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = MAPPING.get(levelname, 37)  # default white
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(PREFIX, seq, levelname, SUFFIX)
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


@click.group()
@click.pass_context
@click.option('--config', '-c', default='config.cfg', help='Path of the auth config file.')
def iotpot(ctx, config):
    # logger
    iotpot_logger = logging.getLogger('iotpot')
    iotpot_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('iotpot.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    my_formatter = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
    cf = ColoredFormatter('%(asctime)-15s %(levelname)s: %(message)s')
    fh.setFormatter(my_formatter)
    ch.setFormatter(cf)
    iotpot_logger.addHandler(fh)
    iotpot_logger.addHandler(ch)
    ctx.obj[LOGGER] = iotpot_logger

    # monitor object always
    ctx.obj[CONFIG] = config
    config_file = ctx.obj['config']
    configuration = Configuration(config_file)
    ctx.obj[CONFIGURATION] = configuration

    # persistent networks and decoys information
    if not os.path.exists(configuration.networks_path):
        os.makedirs(configuration.networks_path)


def monitor_target(monitor):
    monitor.start()


def generator_target(generator):
    generator.start()


def set_configuration(configuration, logger):
    config_set = False
    while not config_set:
        time.sleep(1)
        try:
            print('Trying to set...')
            gnuradio_set_vars(center_freq=configuration.freq,
                              samp_rate=configuration.samp_rate,
                              tx_gain=configuration.tx)

            if gnuradio_get_vars('center_freq') == configuration.freq:
                logger.debug('Center frequency set: ' + str(configuration.freq) + ' Hz')
            if gnuradio_get_vars('samp_rate') == configuration.samp_rate:
                logger.debug('Sample rate set: ' + str(configuration.samp_rate) + ' Hz')
            if gnuradio_get_vars('tx_gain') == configuration.tx:
                logger.debug('TX gain set: ' + str(configuration.tx) + 'db')

            config_set = True
        except:
            pass


@iotpot.command()
@click.pass_context
@click.option('--passive', '-p', is_flag=True)
def run(ctx, passive):
    configuration = ctx.obj[CONFIGURATION]
    logger = ctx.obj[LOGGER]

    if passive:
        network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
        decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)
        receiver = Receiver(configuration, network, decoys, logger, None, None)
        monitor = Monitor(configuration, network, decoys, logger, None, receiver)
        receiver.monitor = monitor
        monitor.start(passive=True)
    else:
        with multiprocessing.Manager() as manager:

            # load networks to shared dictionaries of manager
            network = manager.dict(load_json(configuration.networks_path + '/' + configuration.real_networks_name))
            decoys = manager.dict(load_json(configuration.networks_path + '/' + configuration.virtual_networks_name))

            monitor_conn, generator_conn = Pipe()
            receiver_conn, transmitter_conn = Pipe()

            transmitter = Transmitter(configuration, transmitter_conn)
            responder = Responder(transmitter, decoys, logger)
            receiver = Receiver(configuration, network, decoys, logger, receiver_conn, responder)
            monitor = Monitor(configuration, network, decoys, logger, monitor_conn, receiver)
            receiver.monitor = monitor
            generator = TrafficGenerator(configuration, network, decoys, logger, generator_conn, transmitter)

            # init processes
            monitor_process = Process(target=monitor_target, args=(monitor,))
            configuration_process = Process(target=set_configuration, args=(configuration, logger))

            # start processes
            try:
                configuration_process.start()
                monitor_process.start()
                generator.start()
            except KeyboardInterrupt:
                logger.info('\nTerminating...')
                monitor_process.terminate()
                configuration_process.terminate()

            configuration_process.join()
            monitor_process.join()


@iotpot.command()
@click.pass_context
def record(ctx):
    configuration = ctx.obj[CONFIGURATION]
    logger = ctx.obj[LOGGER]
    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

    receiver = Receiver(configuration, network, decoys, logger, None, None)
    monitor = Monitor(configuration, network, decoys, logger, None, receiver)
    receiver.monitor = monitor
    monitor.record()


@iotpot.command()
@click.pass_context
@click.argument('file')
def read(ctx, file):
    frames = rdpcap(file)
    for frame in frames:
        show_hex(frame)
        frame[ZWaveReq].show()
        print '\n'


@iotpot.command()
@click.pass_context
@click.argument('file')
def test_respond(ctx, file):
    configuration = ctx.obj[CONFIGURATION]
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)
    responder = Responder(None, decoys, None)
    frames = rdpcap(file)
    for frame in frames:
        if ZWaveSwitchBin in frame:
            cmd_class = readable_value(frame[ZWaveReq], Z_CMD_CLASS)
            if cmd_class == CLASS_SWITCH_BINARY:
                cmd = readable_value(frame[ZWaveSwitchBin], Z_CMD)
                if cmd == CMD_GET:
                    frame.show()
                    print '\nrespond:'
                    responder.reply_report(frame)

    print '..............................................................'


if __name__ == '__main__':
    iotpot(obj={})
