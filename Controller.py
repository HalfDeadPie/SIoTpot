import json
import os
from scapy.all import *


import click
import logging

from Configuration import Configuration
from Monitor import Monitor
from TrafficGenerator import TrafficGenerator
from CONSTANTS import MONITOR, CONFIG, LOGGER, MAPPING, PREFIX, SUFFIX, NETWORKS, DECOYS, CONFIGURATION

from copy import copy
from logging import Formatter

from multiprocessing import Process, Pipe


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

    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

    ctx.obj[NETWORKS] = network
    ctx.obj[DECOYS] = decoys

    monitor = Monitor(configuration, network, decoys, iotpot_logger)
    ctx.obj[MONITOR] = monitor


def monitor_target(conn, monitor):
    monitor.start(conn)


def generator_target(conn, generator):
    home_id = conn.recv()
    print 'HOME ID from GENERATOR: ', home_id
    generator.start(home_id)

def set_configuration(configuration, logger):
    config_set = False
    while not config_set:
        time.sleep(1)
        try:
            print('Trying to set...')
            gnuradio_set_vars(center_freq = configuration.freq,
                              samp_rate = configuration.samp_rate,
                              tx_gain = configuration.tx)

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
    monitor = ctx.obj[MONITOR]
    configuration = ctx.obj[CONFIGURATION]
    logger = ctx.obj[LOGGER]
    generator = TrafficGenerator(configuration, ctx.obj[NETWORKS], ctx.obj[DECOYS], logger)
    load_module('gnuradio')

    if passive:
        monitor.start(None)
    else:
        parent_monitor_conn, monitor_conn = Pipe()
        parent_generator_conn, generator_conn = Pipe()

        monitor_process = Process(target=monitor_target, args=(monitor_conn, monitor))
        generator_process = Process(target=generator_target, args=(generator_conn, generator))
        configuration_process = Process(target=set_configuration, args=(configuration, logger))

        monitor_process.start()
        generator_process.start()
        configuration_process.start()
        configuration_process.join()

        home_id = parent_monitor_conn.recv()
        parent_generator_conn.send(home_id)

        monitor_process.join()
        generator_process.join()


@iotpot.command()
@click.pass_context
def record(ctx):
    monitor = ctx.obj[MONITOR]
    monitor.record()


@iotpot.command()
@click.pass_context
@click.argument('file')
def read(ctx, file):
    frames = rdpcap(file)
    for frame in frames:
        frame.show()


if __name__ == '__main__':
    iotpot(obj={})
