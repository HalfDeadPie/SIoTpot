import json
import os
import click
import logging

from Configuration import Configuration
from Monitor import Monitor
from TrafficGenerator import TrafficGenerator
from CONSTANTS import MONITOR, CONFIG, LOGGER, MAPPING, PREFIX, SUFFIX


from copy import copy
from logging import Formatter


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
        seq = MAPPING.get(levelname, 37) # default white
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

    # persistent networks and decoys information
    if not os.path.exists(configuration.networks_path):
        os.makedirs(configuration.networks_path)

    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

    monitor = Monitor(configuration, network, decoys, iotpot_logger)
    ctx.obj[MONITOR] = monitor


@iotpot.command()
@click.pass_context
@click.option('--passive', '-p', is_flag=True)
def run(ctx, passive):
    monitor = ctx.obj[MONITOR]
    configuration = ctx.obj[CONFIG]
    generator = TrafficGenerator(configuration)
    log = ctx.obj[LOGGER]

    if passive:
        monitor.start()
    else:
        pid = os.fork()
        if pid == 0:
            monitor.start()
        else:
            generator.start()


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
