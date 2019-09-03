from Support import *


class Responder:
    def __init__(self, transmitter, decoys, logger):
        self.transmitter = transmitter
        self.decoys = decoys
        self.logger = logger
        #self.stats = {STAT_RES_ACK: 0, STAT_RES_REPORT: 0}

    def reply_ack(self, frame):
        ack_frame = frame[ZWaveReq].copy()
        ack_frame.src, ack_frame.dst = ack_frame.dst, ack_frame.src
        ack_frame.ackreq = Z_ACK_REQ_NO
        ack_frame.headertype = Z_ACK_HEADER_TYPE

        try:
            del (ack_frame[ZWaveSwitchBin])
        except:
            pass
        try:
            del (ack_frame[Raw])
        except:
            pass

        ack_frame.length = calc_length(ack_frame)
        ack_frame.crc = calc_crc(ack_frame)
        self.transmitter.send_frame(ack_frame)

    def reply_report(self, frame):
        report_frame = frame[ZWaveReq].copy()
        report_frame.src, report_frame.dst = report_frame.dst, report_frame.src
        report_frame.ackreq = Z_ACK_REQ_YES
        report_frame.headertype = Z_SW_BINARY_TYPE
        report_frame[ZWaveSwitchBin].cmd = CMD_REPORT
        report_frame.length = calc_length(report_frame)
        report_frame.crc = calc_crc(report_frame)
        report_frame.add_payload(str(self.decoys[text_id(report_frame.homeid)][str(report_frame.src)][DEC_STATE]))
        self.transmitter.send_frame(report_frame)

    def set_state(self, frame):
        self.decoys[text_id(frame.homeid)][str(frame.src)][DEC_STATE] = frame[Raw].load

    def respond(self, frame):
            try:
                self.reply_ack(frame)
                time.sleep(0.1)
                cmd = readable_value(frame[ZWaveSwitchBin], Z_CMD)
                home_id = text_id(frame.homeid)

                if cmd == CMD_SET:
                    if self.decoys[home_id][str(frame.dst)][DEC_STATE] != DEC_STATE_CONTROLLER:
                        self.reply_report(frame)
                        self.logger.debug('Responding ACK, REPORT')

                elif cmd == CMD_GET:
                    if self.decoys[home_id][str(frame.dst)][DEC_STATE] != DEC_STATE_CONTROLLER:
                        self.reply_report(frame)
                        self.logger.debug('Responding ACK, REPORT')

                elif cmd == CMD_REPORT:
                    self.logger.debug('Responding ACK')

            except Exception as e:
                pass
