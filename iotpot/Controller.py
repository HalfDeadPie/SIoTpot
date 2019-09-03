import curses
import multiprocessing
import random
import shutil
import signal
import sys
import time

import click
from scapy.all import *
from Configuration import Configuration
from Monitor import Monitor
from Receiver import Receiver
from Responder import Responder
from TrafficGenerator import TrafficGenerator
from Support import *
from multiprocessing import Process, Pipe
from Transmitter import Transmitter
from Logger import Logger

monitor_stats = {}
responder_stats = {}
iotpot_logger = None


def signal_handler(sig, frame):
    global iotpot_logger
    if bool(monitor_stats):
        report = build_stats_report(monitor_stats)
        if monitor_stats[STAT_MALICIOUS] > 0:
            iotpot_logger.critical(report)
        else:
            iotpot_logger.info(report)

    if bool(responder_stats):
        report = build_stats_report(responder_stats)
        iotpot_logger.info(report)

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def generator_target(generator):
    generator.start()


def receiver_target(receiver, recording, passive):
    signal.signal(signal.SIGINT, signal_handler)
    receiver.start(recording, passive)


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
@click.option('--debug', '-d', help='Level of debug (1-5)', default=1)
@click.pass_context
def iotpot(ctx, config, freq, samp, tx, records, networks, log, alerts, debug):
    """Main command iotpot shares context with other subcommands"""
    ctx.obj[CONFIG] = config
    ctx.obj[DEBUG_LEVEL] = debug
    config_file = ctx.obj['config']
    ctx.obj[CONFIGURATION] = Configuration(config_file, freq, samp, tx, records, networks, log, alerts)

    # create all subdirectories specified in config file
    for path in ctx.obj[CONFIGURATION].paths():
        safe_create_dir(path)

    global iotpot_logger
    iotpot_logger = Logger.initialize_logger(ctx.obj[CONFIGURATION], debug)
    ctx.obj[LOGGER] = iotpot_logger


def stats_view(stats, debug):
    time.sleep(10)
    if debug == 1:
        while True:
            sys.stdout.write("\r")
            for upkey, group in stats.iteritems():
                sys.stdout.write("{} [SET:{}|GET:{}|REPORT:{}|ACK:{}|OTHER:{}] ".format(upkey,
                                                                                        str(group[STAT_SET]),
                                                                                        str(group[STAT_GET]),
                                                                                        str(group[STAT_REPORT]),
                                                                                        str(group[STAT_ACK]),
                                                                                        str(group[STAT_OTHER])))
            sys.stdout.flush()
            time.sleep(1)


@iotpot.command()
@click.pass_context
@click.option('--passive', '-p', is_flag=True,
              help='Passive mode of the IoThoneypot disable any transmitting and allows'
                   'displaying all received frames.')
@click.option('--low', '-l', is_flag=True,
              help='Low-level mode of interaction disables responding, but the traffic is still generated.')
@click.argument('home_id')
def run(ctx, passive, low, home_id=None):
    cfg = ctx.obj[CONFIGURATION]
    cfg.home_id = home_id
    honeylog = ctx.obj[LOGGER]

    with multiprocessing.Manager() as manager:
        network = manager.dict(load_json(cfg.networks_path + '/' + cfg.network_file))
        decoys = manager.dict(load_json(cfg.networks_path + '/' + cfg.decoys_file))

        inner_stats = init_stats_dict()
        stats_malicious = manager.dict(inner_stats.copy())
        stats_invalid = manager.dict(inner_stats.copy())
        stats_in = manager.dict(inner_stats.copy())
        stats_out = manager.dict(inner_stats.copy())

        stats = {STAT_MALICIOUS: stats_malicious,
                 STAT_INVALID: stats_invalid,
                 STAT_IN: stats_in,
                 STAT_OUT: stats_out}

        frames_in = manager.list()
        frames_out = manager.list()

        statsview_process = Process(target=stats_view, args=(stats, ctx.obj[DEBUG_LEVEL]))

        if passive:
            receiver = Receiver(cfg, network, decoys, honeylog, frames_in, frames_out)
            monitor = Monitor(cfg, network, decoys, honeylog, stats)

            receiver.monitor = monitor
            monitor.receiver = receiver

            configuration_process = Process(target=set_configuration, args=(cfg, honeylog))
            configuration_process.start()

            statsview_process.start()
            receiver.start(False, True)

        else:

            if not safe_key_in_dict(home_id, decoys.keys()):
                sys.exit(ERROR_MISSING_DECOYS)

            signal.signal(signal.SIGINT, signal_handler)

            transmitter = Transmitter(cfg, frames_out, stats)

            if not low:  # interaction mode
                responder = Responder(transmitter, decoys, honeylog)
            else:
                responder = None

            receiver = Receiver(cfg, network, decoys, honeylog, frames_in, frames_out, responder)
            monitor = Monitor(cfg, network, decoys, honeylog, stats)

            receiver.monitor = monitor
            monitor.receiver = receiver

            generator = TrafficGenerator(cfg, network, decoys, honeylog, stats, transmitter)

            configuration_process = Process(target=set_configuration, args=(cfg, honeylog))
            receiver_process = Process(target=receiver_target, args=(receiver, False, False))

            try:
                configuration_process.start()
                receiver_process.start()
                statsview_process.start()
                generator.start()
            except KeyboardInterrupt:
                honeylog.info('\nTerminating...')
                receiver_process.terminate()
                configuration_process.terminate()

            configuration_process.join()
            receiver_process.join()
            statsview_process.join()


@iotpot.command()
@click.pass_context
def record(ctx):
    """Records frames until users interrupt"""
    cfg = ctx.obj[CONFIGURATION]
    honeylog = ctx.obj[LOGGER]
    network = load_json(load_json(cfg.networks_path + '/' + cfg.network_file))
    decoys = load_json(load_json(cfg.networks_path + '/' + cfg.decoys_file))
    receiver = Receiver(cfg, network, decoys, honeylog, None, None)
    monitor = Monitor(cfg, network, decoys, honeylog, None, receiver)
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
    cfg = ctx.obj[CONFIGURATION]
    network = load_json(cfg.path_network_file())
    decoys = load_json(cfg.path_decoys_file())

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
