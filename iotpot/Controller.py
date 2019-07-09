import multiprocessing
import random
import shutil
import signal
import sys

import click
import logging
from scapy.all import *
from Configuration import Configuration
from Monitor import Monitor
from Receiver import Receiver
from Responder import Responder
from TrafficGenerator import TrafficGenerator
from Support import *
from copy import copy
from logging import Formatter
from multiprocessing import Process, Pipe
from Transmitter import Transmitter

monitor_stats = {}
responder_stats = {}
iotpot_logger = None


def signal_handler(sig, frame):
    global iotpot_logger
    if bool(monitor_stats):
        report = build_stats_report(monitor_stats)
        print 'Monitor statistics:'
        if monitor_stats[STAT_MALICIOUS] > 0:
            iotpot_logger.critical(report)
        else:
            iotpot_logger.info(report)

    if bool(responder_stats):
        print 'Responder statistics:'
        report = build_stats_report(responder_stats)
        iotpot_logger.info(report)

    sys.exit(0)


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
        seq = MAPPING.get(levelname, 37)  # 0xdf11f630 white
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(PREFIX, seq, levelname, SUFFIX)
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


@click.group()
@click.option('--config', '-c', default='config.cfg', help='Path of the configuration file')
@click.option('--freq', '-f', help='The frequency of the receiver and the transmitter. Default value is 868420000')
@click.option('--samp', '-s', help='The sample rate of the receiver, The sample rate of '
                                   'the transmitter is multiplied by 10x. Default value is 2000000')
@click.option('--tx', '-t', help='TX gain of the transmitter. Default value is 25')
@click.option('--records', '-r', help='The path of the records')
@click.option('--networks', '-n', help='The path of the networks. Default value is networks')
@click.option('--log', '-l', help='Path to a logging file')
@click.option('--alerts', '-a', help='Path to a alert logging file')
@click.pass_context
def iotpot(ctx, config, freq, samp, tx, records, networks, log, alerts):
    """Main command iotpot shares context with other subcommands"""
    ctx.obj[CONFIG] = config
    config_file = ctx.obj['config']
    configuration = Configuration(config_file, freq, samp, tx, records, networks, log, alerts)
    ctx.obj[CONFIGURATION] = configuration

    global iotpot_logger
    iotpot_logger = logging.getLogger('iotpot')
    iotpot_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(configuration.logging_file)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ah = logging.FileHandler(configuration.alerts_file)
    ah.setLevel(logging.WARNING)
    my_formatter = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
    cf = ColoredFormatter('%(asctime)-15s %(levelname)s: %(message)s')
    fh.setFormatter(my_formatter)
    ch.setFormatter(cf)
    ah.setFormatter(my_formatter)
    iotpot_logger.addHandler(fh)
    iotpot_logger.addHandler(ch)
    iotpot_logger.addHandler(ah)
    ctx.obj[LOGGER] = iotpot_logger

    # persistent networks and decoys information
    if not os.path.exists(configuration.networks_path):
        os.makedirs(configuration.networks_path)


def generator_target(generator):
    generator.start()


def monitor_target(monitor):
    signal.signal(signal.SIGINT, signal_handler)
    global monitor_stats
    monitor_stats = monitor.stats

    global responder_stats
    responder_stats = monitor.receiver.responder.stats
    monitor.start()


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
                logger.info('Center frequency set: ' + str(configuration.freq) + ' Hz')
            if gnuradio_get_vars('samp_rate') == configuration.samp_rate:
                logger.info('Sample rate set: ' + str(configuration.samp_rate) + ' Hz')
            if gnuradio_get_vars('tx_gain') == configuration.tx:
                logger.info('TX gain set: ' + str(configuration.tx) + 'db')

            config_set = True
        except Exception as e:
            print e


@iotpot.command()
@click.pass_context
@click.option('--passive', '-p', is_flag=True,
              help='Passive mode of the IoThoneypot disable any transmitting and allows'
                   'displaying all received frames.')
@click.option('--low', '-l', is_flag=True,
              help='Low-level mode of interaction disables responding, but the traffic is still generated.')
@click.argument('home_id', required=False)
@click.option('--test', '-t', hidden=True)
def run(ctx, passive, low, home_id, test):
    """Starts the IoT honeypot"""
    configuration = ctx.obj[CONFIGURATION]
    configuration.home_id = home_id
    if test:
        configuration.home_id = DEFAULT_HOME_ID
    logger = ctx.obj[LOGGER]

    if passive:
        signal.signal(signal.SIGINT, signal_handler)
        network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
        decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

        receiver = Receiver(configuration, network, decoys, logger, None, None)
        monitor = Monitor(configuration, network, decoys, logger, None, receiver)
        receiver.monitor = monitor

        configuration_process = Process(target=set_configuration, args=(configuration, logger))
        configuration_process.start()

        signal.signal(signal.SIGINT, signal_handler)
        global monitor_stats
        monitor_stats = monitor.stats

        monitor.start(passive=True)

    else:
        with multiprocessing.Manager() as manager:

            # load networks to shared dictionaries of manager
            network = manager.dict(load_json(configuration.networks_path + '/' + configuration.real_networks_name))
            decoys = manager.dict(load_json(configuration.networks_path + '/' + configuration.virtual_networks_name))

            if home_id and home_id not in decoys.keys():
                sys.exit(ERROR_MISSING_DECOYS)

            signal.signal(signal.SIGINT, signal_handler)

            monitor_conn, generator_conn = Pipe()
            receiver_conn, transmitter_conn = Pipe()

            transmitter = Transmitter(configuration, transmitter_conn)
            if not low:
                responder = Responder(transmitter, decoys, logger)
            else:
                responder = None
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
                generator.start(test)
            except Exception as e:
                print e
            except KeyboardInterrupt:
                logger.info('\nTerminating...')
                monitor_process.terminate()
                configuration_process.terminate()

            configuration_process.join()
            monitor_process.join()


@iotpot.command()
@click.pass_context
def record(ctx):
    """Records frames until users interrupt"""
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
@click.argument('home_id')
def add(ctx, home_id):
    """Add single new device to a network information"""
    configuration = ctx.obj[CONFIGURATION]
    configuration.home_id = home_id
    logger = ctx.obj[LOGGER]
    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)
    receiver = Receiver(configuration, network, decoys, logger, None, None)
    receiver.add_device(home_id)


@iotpot.command()
@click.pass_context
@click.argument('home_id')
@click.argument('node_id')
def delete(ctx, home_id, node_id):
    """Remove single decoy and its corresponding records"""
    configuration = ctx.obj[CONFIGURATION]
    configuration.home_id = home_id
    logger = ctx.obj[LOGGER]
    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)
    records_to_delete = remove_duplicate_decoys(home_id, node_id, decoys, configuration)
    remove_unrecorded_decoys(decoys, home_id, records_to_delete)
    save_networks(configuration, network, decoys)


@iotpot.command()
@click.pass_context
@click.argument('home_id_from')
@click.argument('home_id_to', required=False)
def replicate(ctx, home_id_from, home_id_to):
    """Replicate records and data from home_id_from to home_id_to"""
    configuration = ctx.obj[CONFIGURATION]
    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

    if not home_id_to:
        home_id_to = home_id_from

    safe_create_dir(configuration.records_path + '/' + home_id_to)

    if home_id_from in decoys:
        decoys_from = decoys[home_id_from].keys()
        decoys_from = [int(x) for x in decoys_from]
    else:
        sys.exit(ERROR_MISSING_NETWORK)

    if home_id_to in network.keys():
        real_nodes_to = network[home_id_to]
    else:
        real_nodes_to = []
        print '\n' + WARNING_NO_REAL + '\n'

    if home_id_to in decoys:
        decoys_to = decoys[home_id_to].keys()
        decoys_to = [int(x) for x in decoys_to]
    else:
        decoys_to = []

    all_nodes_to = real_nodes_to + decoys_to
    free_ids = list_free_ids(all_nodes_to)

    mapping = {}
    for decoy_from in decoys_from:
        if decoys[home_id_from][str(decoy_from)][DEC_STATE] == DEC_STATE_CONTROLLER:
            mapping[decoy_from] = free_ids[1]
        else:
            mapping[decoy_from] = random.choice(free_ids)
        free_ids.remove(mapping[decoy_from])

    record_frames = load_decoys_frames(configuration.records_path + '/' + home_id_from)

    for r in record_frames:
        if r.src in mapping.keys():
            r.src = mapping[r.src]
        if r.dst in mapping.keys():
            r.dst = mapping[r.dst]
        r.homeid = int(home_id_to, 0)

    time_text = str(time.strftime(FILE_TIME_FORMAT))
    record_name = 'copy_' + home_id_from + '_' + time_text + RECORD_EXTENSION

    for from_decoy, new_decoy in mapping.iteritems():
        safe_create_dict_dict(decoys, home_id_to)
        safe_create_dict_dict(decoys[home_id_to], str(new_decoy))
        safe_create_dict_list(decoys[home_id_to][str(new_decoy)], DEC_RECORD)
        safe_append(decoys[home_id_to][str(new_decoy)][DEC_RECORD], record_name)
        if decoys[home_id_from][str(from_decoy)][DEC_STATE] == DEC_STATE_CONTROLLER:
            decoys[home_id_to][str(new_decoy)][DEC_STATE] = unicode(DEC_STATE_CONTROLLER)
        else:
            decoys[home_id_to][str(new_decoy)][DEC_STATE] = unicode(DEC_STATE_OFF)

    wrpcap(configuration.records_path + '/' + home_id_to + '/' + record_name, record_frames)
    if decoys:
        json.dump(decoys,
                  open(configuration.networks_path + '/' +
                       configuration.virtual_networks_name, 'w'))


@iotpot.command()
@click.pass_context
def status(ctx):
    """Display persistent information of the IoT honeypot"""
    configuration = ctx.obj[CONFIGURATION]
    network = load_json(configuration.networks_path + '/' + configuration.real_networks_name)
    decoys = load_json(configuration.networks_path + '/' + configuration.virtual_networks_name)

    for home_id, network_dict in decoys.iteritems():
        print home_id + ' . . . . . . . . . . . . . . . . '
        if home_id in network.keys():
            print '\tnodes:\t',
            for n in network[home_id]:
                print str(n) + ' ',

            print ''

        print '\tdecoys:'
        for decoy, decoy_status in network_dict.iteritems():
            print '\t\t' + str(decoy) + '\t'
            for record in decoy_status[DEC_RECORD]:
                print '\t\t\t' + record
        print ''


@iotpot.command()
@click.pass_context
@click.argument('file')
def read(ctx, file):
    """Display records in human-readable form"""
    frames = rdpcap(file)
    for frame in frames:
        show_hex(frame)
        frame[ZWaveReq].show()
        print '\n'


@iotpot.command()
@click.pass_context
def reset(ctx):
    """Remove all persistent information"""
    configuration = ctx.obj[CONFIGURATION]

    # remove records
    try:
        records = [f for f in os.listdir(configuration.records_path)]
        for f in records:
            shutil.rmtree(configuration.records_path + '/' + f)
    except:
        pass

    try:
        networks = [f for f in os.listdir(configuration.networks_path)]
        for f in networks:
            os.remove(os.path.join(configuration.networks_path, f))
    except Exception as e:
        print e


if __name__ == '__main__':
    iotpot(obj={})
