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

responder_stats = {}
iotpot_logger = None


def signal_handler(sig, frame):
    """
    Exiting signal handler
    """
    global iotpot_logger

    if bool(responder_stats):
        report = build_stats_report(responder_stats)
        iotpot_logger.info(report)

    sys.exit(0)


def generator_target(generator):
    """
    Starts the generator
    :param generator: generator of simulated communication
    """
    generator.start()


def receiver_target(receiver, recording, passive):
    """
    Starts the receiver
    :param receiver: receiver of communication
    :param recording: mode for recording communication
    :param passive: mode for passive monitoring
    """
    signal.signal(signal.SIGINT, signal_handler)
    receiver.start(recording, passive)


def set_configuration(configuration, logger):
    """
    Set the configuration according to configuration file or switches
    :param configuration: includes several attributes
    :param logger: for initialization of logging activities
    """
    config_set = False
    while not config_set:
        try:
            gnuradio_set_vars(center_freq=int(configuration.freq),
                              samp_rate=int(configuration.samp_rate),
                              tx_gain=int(configuration.tx))

            if gnuradio_get_vars('center_freq') == configuration.freq:
                logger.info('Center frequency set: ' + str(configuration.freq) + ' Hz')
            if gnuradio_get_vars('samp_rate') == configuration.samp_rate:
                logger.info('Sample rate set: ' + str(configuration.samp_rate) + ' Hz')
            if gnuradio_get_vars('tx_gain') == configuration.tx:
                logger.info('TX gain set: ' + str(configuration.tx) + 'db')

            config_set = True
        except Exception as e:
            pass
            # print e # uncommenting this causes connecting to socket which may not be ready at the start


def stats_view(stats, honeypot_debug_level):
    """
    Display current stats of every group which includes SET, GET, REPORT, ACK and OTHER commands
    :param stats: dictionary composed of statistics shared between several processes
    :param honeypot_debug_level: debugging
    """
    if honeypot_debug_level is 1:
        while True:
            sys.stdout.write("\r")
            for upkey, group in stats.iteritems():
                sys.stdout.write(
                    "{} [S:{}|G:{}|R:{}|A:{}|O:{}] ".format(upkey,
                                                            str(group[STAT_SET]),
                                                            str(group[STAT_GET]),
                                                            str(group[STAT_REPORT]),
                                                            str(group[STAT_ACK]),
                                                            str(group[STAT_OTHER])))
            sys.stdout.flush()
            time.sleep(1)


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
def siotpot(ctx, config, freq, samp, tx, records, networks, log, alerts, debug):
    """
    Main command that is used always with every other subcommand and share context with them
    :param ctx: shared context
    :param config: configuration of the honeypot
    :param freq: RX and TX frequency
    :param samp: sample rate of the receiver
    :param tx: TX gain of the transmitter
    :param records: path to record files
    :param networks: path to network information
    :param log: path to logging file
    :param alerts: path to alert file
    :param debug: debugging level (1-5)
    :return:
    """
    # share configuration, debugging level
    ctx.obj[CONFIG] = config
    ctx.obj[DEBUG_LEVEL] = debug
    config_file = ctx.obj['config']
    ctx.obj[CONFIGURATION] = Configuration(config_file, freq, samp, tx, records, networks, log, alerts)

    # create all subdirectories specified in config file
    for path in ctx.obj[CONFIGURATION].paths():
        safe_create_dir(path)

    # initialize logger
    global iotpot_logger
    iotpot_logger = Logger.initialize_logger(ctx.obj[CONFIGURATION], debug)
    ctx.obj[LOGGER] = iotpot_logger


@siotpot.command()
@click.pass_context
@click.option('--verbose', '-v', is_flag=True, help='Display received frames.')
@click.argument('home_id', required=False)
def listen(ctx, verbose, home_id):
    """
    Passive monitoring of network
    :param ctx: shared context
    :param verbose: show received frames
    :param home_id: filter frames including specified home-id
    """
    # initialize
    signal.signal(signal.SIGINT, signal_handler)
    cfg = ctx.obj[CONFIGURATION]
    cfg.home_id = home_id
    cfg.verbose = verbose
    honeylog = ctx.obj[LOGGER]

    with multiprocessing.Manager() as manager:
        # initialize shared network and decoy information
        network = manager.dict(load_json(cfg.networks_path + '/' + cfg.network_file))
        decoys = manager.dict(load_json(cfg.networks_path + '/' + cfg.decoys_file))

        # init stats
        inner_stats = init_stats_dict()
        stats_real = manager.dict(inner_stats.copy())
        stats_malicious = manager.dict(inner_stats.copy())
        stats_invalid = manager.dict(inner_stats.copy())
        stats_in = manager.dict(inner_stats.copy())
        stats_out = manager.dict(inner_stats.copy())

        stats = {STAT_REAL: stats_real,
                 STAT_MALICIOUS: stats_malicious,
                 STAT_INVALID: stats_invalid,
                 STAT_IN: stats_in,
                 STAT_OUT: stats_out}

        frames_in = list()
        frames_out = list()

        # initialize components
        receiver = Receiver(cfg, network, decoys, honeylog, frames_in, frames_out)
        monitor = Monitor(cfg, network, decoys, honeylog, stats)

        receiver.monitor = monitor
        monitor.receiver = receiver

        # start configuration
        configuration_process = Process(target=set_configuration, args=(cfg, honeylog))
        configuration_process.start()

        # if not verbose
        if not verbose:
            # show only stats
            statsview_process = Process(target=stats_view, args=(stats, ctx.obj[DEBUG_LEVEL]))
            statsview_process.start()

        # start reception
        receiver.start(False, True)


@siotpot.command()
@click.pass_context
@click.option('--low', '-l', is_flag=True,
              help='Low-level mode of interaction disables responding, but the traffic is still generated.')
@click.argument('home_id')
def run(ctx, low, home_id):
    """
    Run main function of the IoT honeypot
    :param ctx: shared context
    :param low: low-interaction mode means that the honeypot does not respond to malicious frames
    :param home_id: specifies the network identifier
    """
    # initialization
    signal.signal(signal.SIGINT, signal_handler)
    cfg = ctx.obj[CONFIGURATION]
    cfg.home_id = home_id
    honeylog = ctx.obj[LOGGER]

    # manager handles shared content between TX and RX processes
    with multiprocessing.Manager() as manager:
        network = manager.dict(load_json(cfg.networks_path + '/' + cfg.network_file))
        decoys = manager.dict(load_json(cfg.networks_path + '/' + cfg.decoys_file))

        # init stats
        inner_stats = init_stats_dict()
        stats_real = manager.dict(inner_stats.copy())
        stats_malicious = manager.dict(inner_stats.copy())
        stats_invalid = manager.dict(inner_stats.copy())
        stats_in = manager.dict(inner_stats.copy())
        stats_out = manager.dict(inner_stats.copy())

        stats = {STAT_REAL: stats_real,
                 STAT_MALICIOUS: stats_malicious,
                 STAT_INVALID: stats_invalid,
                 STAT_IN: stats_in,
                 STAT_OUT: stats_out}

        frames_in = manager.list()
        frames_out = manager.list()

        # display real-time statistics
        statsview_process = Process(target=stats_view, args=(stats, ctx.obj[DEBUG_LEVEL]))

        # if records for specified network are missing
        if not safe_key_in_dict(home_id, decoys.keys()):
            # honeypot stops and display error
            sys.exit(ERROR_MISSING_DECOYS)

        signal.signal(signal.SIGINT, signal_handler)

        # init frame transmitter
        transmitter = Transmitter(cfg, frames_out, stats)

        # if not low-interaction mode
        if not low:
            # init responder
            responder = Responder(transmitter, decoys, honeylog)
        else:
            # else responder not needed
            responder = None

        # init receiver and monitor
        receiver = Receiver(cfg, network, decoys, honeylog, frames_in, frames_out, responder)
        monitor = Monitor(cfg, network, decoys, honeylog, stats)

        receiver.monitor = monitor
        monitor.receiver = receiver

        # init traffic generator
        generator = TrafficGenerator(cfg, network, decoys, honeylog, stats, transmitter)

        # honeypot configuration process
        configuration_process = Process(target=set_configuration, args=(cfg, honeylog))

        # receiver process
        receiver_process = Process(target=receiver_target, args=(receiver, False, False))

        try:
            configuration_process.start()
            receiver_process.start()
            statsview_process.start()
            # generator works in main process
            generator.start()
        except KeyboardInterrupt:
            honeylog.info('\nTerminating...')
            receiver_process.terminate()
            configuration_process.terminate()

        configuration_process.join()
        receiver_process.join()
        statsview_process.join()


@siotpot.command()
@click.pass_context
def record(ctx):
    """
    Maps real network, record its communication, anonymize it.
    Records are saved into pcap files. Network and decoy information are saved into json files.
    :param ctx: shared context
    """
    cfg = ctx.obj[CONFIGURATION]
    honeylog = ctx.obj[LOGGER]

    network = load_json(cfg.networks_path + '/' + cfg.network_file)
    decoys = load_json(cfg.networks_path + '/' + cfg.decoys_file)

    receiver = Receiver(cfg, network, decoys, honeylog, None, None)
    receiver.start(recording=True)


@siotpot.command()
@click.pass_context
@click.argument('home_id_from')
@click.argument('home_id_to', required=False)
def replicate(ctx, home_id_from, home_id_to):
    """
    Replicate decoy information and records from one network to anoter. Using a single argument causes
    extending specified network.
    :param ctx: shared context
    :param home_id_from: source network
    :param home_id_to: destination network
    :return:
    """
    # init information
    configuration = ctx.obj[CONFIGURATION]
    network = load_json(configuration.networks_path + '/' + configuration.network_file)
    decoys = load_json(configuration.networks_path + '/' + configuration.decoys_file)

    # check number of arguments
    if not home_id_to:
        home_id_to = home_id_from

    # create directory for new network
    safe_create_dir(configuration.records_path + '/' + home_id_to)

    # check existence of source network
    if home_id_from in decoys:
        decoys_from = decoys[home_id_from].keys()
        decoys_from = [int(x) for x in decoys_from]
    else:
        sys.exit(ERROR_MISSING_NETWORK)

    # check existence of mapping of the real destination network
    # (unmapped network can cause NodeID collisions with decoys from source network)
    if home_id_to in network.keys():
        real_nodes_to = network[home_id_to]
    else:
        real_nodes_to = []
        print '\n' + WARNING_NO_REAL + '\n'

    # check existence of destination's decoys
    if home_id_to in decoys:
        decoys_to = decoys[home_id_to].keys()
        decoys_to = [int(x) for x in decoys_to]
    else:
        decoys_to = []

    # get list of free NodeId
    all_nodes_to = real_nodes_to + decoys_to
    free_ids = list_free_ids(all_nodes_to)

    # create mapping
    mapping = {}
    for decoy_from in decoys_from:
        if decoys[home_id_from][str(decoy_from)][DEC_STATE] == DEC_STATE_CONTROLLER:
            mapping[decoy_from] = free_ids[1]
        else:
            mapping[decoy_from] = random.choice(free_ids)
        free_ids.remove(mapping[decoy_from])

    # load source records
    record_frames = load_decoys_frames(configuration.records_path + '/' + home_id_from)

    # swap identificators according to mapping
    for r in record_frames:
        if r.src in mapping.keys():
            r.src = mapping[r.src]
        if r.dst in mapping.keys():
            r.dst = mapping[r.dst]
        r.homeid = int(home_id_to, 0)

    # get current time
    time_text = str(time.strftime(FILE_TIME_FORMAT))

    # name for the new record
    record_name = 'copy_' + home_id_from + '_' + time_text + RECORD_EXTENSION

    # create the new information
    for from_decoy, new_decoy in mapping.iteritems():
        safe_create_dict_dict(decoys, home_id_to)
        safe_create_dict_dict(decoys[home_id_to], str(new_decoy))
        safe_create_dict_list(decoys[home_id_to][str(new_decoy)], DEC_RECORD)
        safe_append(decoys[home_id_to][str(new_decoy)][DEC_RECORD], record_name)
        if decoys[home_id_from][str(from_decoy)][DEC_STATE] == DEC_STATE_CONTROLLER:
            decoys[home_id_to][str(new_decoy)][DEC_STATE] = unicode(DEC_STATE_CONTROLLER)
        else:
            decoys[home_id_to][str(new_decoy)][DEC_STATE] = unicode(DEC_STATE_OFF)

    # save the record
    wrpcap(configuration.records_path + '/' + home_id_to + '/' + record_name, record_frames)
    if decoys:
        json.dump(decoys,
                  open(configuration.networks_path + '/' +
                       configuration.decoys_file, 'w'))


@siotpot.command()
@click.pass_context
def status(ctx):
    """
    Display persistent information like network, decoy information and its records
    :param ctx: shared context
    """
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


@siotpot.command()
@click.pass_context
@click.argument('file')
def read(ctx, file):
    """
    Display records in human-readable form
    :param ctx: shared context
    :param file: record to be displayed
    """
    frames = rdpcap(file)
    for frame in frames:
        show_hex(frame)
        frame[ZWaveReq].show()
        print '\n'


@siotpot.command()
@click.pass_context
def reset(ctx):
    """
    WARNING! Remove all persistent information!
    :param ctx: shared context
    """
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
    siotpot(obj={})
