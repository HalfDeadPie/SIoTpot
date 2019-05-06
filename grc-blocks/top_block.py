#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Sun May  5 19:35:22 2019
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.wxgui import forms
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import SimpleXMLRPCServer
import Zwave
import math
import osmosdr
import threading
import time
import wx


class top_block(grc_wxgui.top_block_gui):

    def __init__(self):
        grc_wxgui.top_block_gui.__init__(self, title="Top Block")
        _icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 2e6
        self.r2_baud = r2_baud = 40e3
        self.r1_freq_offset = r1_freq_offset = 80e3
        self.r1_baud = r1_baud = 19.2e3
        self.tx_sps = tx_sps = 2
        self.tx_gain = tx_gain = 35
        self.tx_freq_offset_1 = tx_freq_offset_1 = 14e3
        self.tx_freq_offset = tx_freq_offset = -25e3
        self.taps = taps = firdes.low_pass(1,samp_rate,150e3,50e3,firdes.WIN_HAMMING)
        self.rx_if_gain = rx_if_gain = 24
        self.rx_freq_offset = rx_freq_offset = 0
        self.rx_bb_gain = rx_bb_gain = 24
        self.r3_freq_offset = r3_freq_offset = 30e3
        self.r2_sps = r2_sps = int(samp_rate/r2_baud)
        self.r2_freq_offset = r2_freq_offset = r1_freq_offset+2e4
        self.r1_sps = r1_sps = int(samp_rate/r1_baud)
        self.preamble_len = preamble_len = 80
        self.center_freq = center_freq = 868420000

        ##################################################
        # Blocks
        ##################################################
        _tx_freq_offset_sizer = wx.BoxSizer(wx.VERTICAL)
        self._tx_freq_offset_text_box = forms.text_box(
        	parent=self.GetWin(),
        	sizer=_tx_freq_offset_sizer,
        	value=self.tx_freq_offset,
        	callback=self.set_tx_freq_offset,
        	label="Transmitting Frequency Offset",
        	converter=forms.float_converter(),
        	proportion=0,
        )
        self._tx_freq_offset_slider = forms.slider(
        	parent=self.GetWin(),
        	sizer=_tx_freq_offset_sizer,
        	value=self.tx_freq_offset,
        	callback=self.set_tx_freq_offset,
        	minimum=-200e3,
        	maximum=200e3,
        	num_steps=1000,
        	style=wx.SL_HORIZONTAL,
        	cast=float,
        	proportion=1,
        )
        self.Add(_tx_freq_offset_sizer)
        _rx_freq_offset_sizer = wx.BoxSizer(wx.VERTICAL)
        self._rx_freq_offset_text_box = forms.text_box(
        	parent=self.GetWin(),
        	sizer=_rx_freq_offset_sizer,
        	value=self.rx_freq_offset,
        	callback=self.set_rx_freq_offset,
        	label="Receiving Frequency Offset",
        	converter=forms.float_converter(),
        	proportion=0,
        )
        self._rx_freq_offset_slider = forms.slider(
        	parent=self.GetWin(),
        	sizer=_rx_freq_offset_sizer,
        	value=self.rx_freq_offset,
        	callback=self.set_rx_freq_offset,
        	minimum=-200e3,
        	maximum=200e3,
        	num_steps=1000,
        	style=wx.SL_HORIZONTAL,
        	cast=float,
        	proportion=1,
        )
        self.Add(_rx_freq_offset_sizer)
        self.xmlrpc_server_0 = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8080), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(center_freq + rx_freq_offset, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(14, 0)
        self.rtlsdr_source_0.set_if_gain(24, 0)
        self.rtlsdr_source_0.set_bb_gain(24, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)
          
        self.rational_resampler_xxx_1 = filter.rational_resampler_ccc(
                interpolation=250,
                decimation=1,
                taps=None,
                fractional_bw=None,
        )
        self.osmosdr_sink_0 = osmosdr.sink( args="numchan=" + str(1) + " " + "" )
        self.osmosdr_sink_0.set_sample_rate(samp_rate*10)
        self.osmosdr_sink_0.set_center_freq(center_freq+tx_freq_offset, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(18, 0)
        self.osmosdr_sink_0.set_if_gain(tx_gain, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna("", 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
          
        self.low_pass_filter_0_0 = filter.fir_filter_fff(1, firdes.low_pass(
        	1, samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.low_pass_filter_0 = filter.fir_filter_fff(1, firdes.low_pass(
        	1, samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.freq_xlating_fir_filter_xxx_0_0 = filter.freq_xlating_fir_filter_ccc(1, (taps), -1*r2_freq_offset, samp_rate)
        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_ccc(1, (taps), -1*r1_freq_offset, samp_rate)
        self.digital_gfsk_mod_0 = digital.gfsk_mod(
        	samples_per_symbol=tx_sps,
        	sensitivity=2,
        	bt=1,
        	verbose=False,
        	log=False,
        )
        self.digital_clock_recovery_mm_xx_0_0 = digital.clock_recovery_mm_ff(r2_sps, 0.25*0.175*0.175, 0.5, 0.175, 0.005)
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(r2_sps, 0.25*0.175*0.175, 0.5, 0.175, 0.005)
        self.digital_binary_slicer_fb_0_0 = digital.binary_slicer_fb()
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.blocks_socket_pdu_0_0 = blocks.socket_pdu("UDP_CLIENT", "127.0.0.1", "52002", 10000, False)
        self.blocks_socket_pdu_0 = blocks.socket_pdu("UDP_SERVER", "127.0.0.1", "52001", 10000, False)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, "packet_len")
        self.blocks_not_xx_0 = blocks.not_bb()
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.9, ))
        self.analog_simple_squelch_cc_0_0 = analog.simple_squelch_cc(-40, 1)
        self.analog_simple_squelch_cc_0 = analog.simple_squelch_cc(-40, 1)
        self.analog_quadrature_demod_cf_0_0 = analog.quadrature_demod_cf(2*(samp_rate)/(2*math.pi*20e3/8.0))
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(2*(samp_rate)/(2*math.pi*20e3/8.0))
        self.Zwave_preamble_0 = Zwave.preamble(preamble_len)
        self.Zwave_packet_sink_0_1 = Zwave.packet_sink()
        self.Zwave_packet_sink_0 = Zwave.packet_sink()

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.Zwave_packet_sink_0, 'out'), (self.blocks_socket_pdu_0_0, 'pdus'))    
        self.msg_connect((self.Zwave_packet_sink_0_1, 'out'), (self.blocks_socket_pdu_0_0, 'pdus'))    
        self.msg_connect((self.Zwave_preamble_0, 'out'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))    
        self.msg_connect((self.blocks_socket_pdu_0, 'pdus'), (self.Zwave_preamble_0, 'in'))    
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.low_pass_filter_0, 0))    
        self.connect((self.analog_quadrature_demod_cf_0_0, 0), (self.low_pass_filter_0_0, 0))    
        self.connect((self.analog_simple_squelch_cc_0, 0), (self.analog_quadrature_demod_cf_0, 0))    
        self.connect((self.analog_simple_squelch_cc_0_0, 0), (self.analog_quadrature_demod_cf_0_0, 0))    
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.rational_resampler_xxx_1, 0))    
        self.connect((self.blocks_not_xx_0, 0), (self.digital_gfsk_mod_0, 0))    
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.blocks_not_xx_0, 0))    
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.Zwave_packet_sink_0_1, 0))    
        self.connect((self.digital_binary_slicer_fb_0_0, 0), (self.Zwave_packet_sink_0, 0))    
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_binary_slicer_fb_0, 0))    
        self.connect((self.digital_clock_recovery_mm_xx_0_0, 0), (self.digital_binary_slicer_fb_0_0, 0))    
        self.connect((self.digital_gfsk_mod_0, 0), (self.blocks_multiply_const_vxx_0, 0))    
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.analog_simple_squelch_cc_0, 0))    
        self.connect((self.freq_xlating_fir_filter_xxx_0_0, 0), (self.analog_simple_squelch_cc_0_0, 0))    
        self.connect((self.low_pass_filter_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))    
        self.connect((self.low_pass_filter_0_0, 0), (self.digital_clock_recovery_mm_xx_0_0, 0))    
        self.connect((self.rational_resampler_xxx_1, 0), (self.osmosdr_sink_0, 0))    
        self.connect((self.rtlsdr_source_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))    
        self.connect((self.rtlsdr_source_0, 0), (self.freq_xlating_fir_filter_xxx_0_0, 0))    

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_r1_sps(int(self.samp_rate/self.r1_baud))
        self.set_r2_sps(int(self.samp_rate/self.r2_baud))
        self.set_taps(firdes.low_pass(1,self.samp_rate,150e3,50e3,firdes.WIN_HAMMING))
        self.analog_quadrature_demod_cf_0.set_gain(2*(self.samp_rate)/(2*math.pi*20e3/8.0))
        self.analog_quadrature_demod_cf_0_0.set_gain(2*(self.samp_rate)/(2*math.pi*20e3/8.0))
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate*10)
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)

    def get_r2_baud(self):
        return self.r2_baud

    def set_r2_baud(self, r2_baud):
        self.r2_baud = r2_baud
        self.set_r2_sps(int(self.samp_rate/self.r2_baud))

    def get_r1_freq_offset(self):
        return self.r1_freq_offset

    def set_r1_freq_offset(self, r1_freq_offset):
        self.r1_freq_offset = r1_freq_offset
        self.set_r2_freq_offset(self.r1_freq_offset+2e4)
        self.freq_xlating_fir_filter_xxx_0.set_center_freq(-1*self.r1_freq_offset)

    def get_r1_baud(self):
        return self.r1_baud

    def set_r1_baud(self, r1_baud):
        self.r1_baud = r1_baud
        self.set_r1_sps(int(self.samp_rate/self.r1_baud))

    def get_tx_sps(self):
        return self.tx_sps

    def set_tx_sps(self, tx_sps):
        self.tx_sps = tx_sps

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.osmosdr_sink_0.set_if_gain(self.tx_gain, 0)

    def get_tx_freq_offset_1(self):
        return self.tx_freq_offset_1

    def set_tx_freq_offset_1(self, tx_freq_offset_1):
        self.tx_freq_offset_1 = tx_freq_offset_1

    def get_tx_freq_offset(self):
        return self.tx_freq_offset

    def set_tx_freq_offset(self, tx_freq_offset):
        self.tx_freq_offset = tx_freq_offset
        self.osmosdr_sink_0.set_center_freq(self.center_freq+self.tx_freq_offset, 0)
        self._tx_freq_offset_slider.set_value(self.tx_freq_offset)
        self._tx_freq_offset_text_box.set_value(self.tx_freq_offset)

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps
        self.freq_xlating_fir_filter_xxx_0.set_taps((self.taps))
        self.freq_xlating_fir_filter_xxx_0_0.set_taps((self.taps))

    def get_rx_if_gain(self):
        return self.rx_if_gain

    def set_rx_if_gain(self, rx_if_gain):
        self.rx_if_gain = rx_if_gain

    def get_rx_freq_offset(self):
        return self.rx_freq_offset

    def set_rx_freq_offset(self, rx_freq_offset):
        self.rx_freq_offset = rx_freq_offset
        self.rtlsdr_source_0.set_center_freq(self.center_freq + self.rx_freq_offset, 0)
        self._rx_freq_offset_slider.set_value(self.rx_freq_offset)
        self._rx_freq_offset_text_box.set_value(self.rx_freq_offset)

    def get_rx_bb_gain(self):
        return self.rx_bb_gain

    def set_rx_bb_gain(self, rx_bb_gain):
        self.rx_bb_gain = rx_bb_gain

    def get_r3_freq_offset(self):
        return self.r3_freq_offset

    def set_r3_freq_offset(self, r3_freq_offset):
        self.r3_freq_offset = r3_freq_offset

    def get_r2_sps(self):
        return self.r2_sps

    def set_r2_sps(self, r2_sps):
        self.r2_sps = r2_sps
        self.digital_clock_recovery_mm_xx_0.set_omega(self.r2_sps)
        self.digital_clock_recovery_mm_xx_0_0.set_omega(self.r2_sps)

    def get_r2_freq_offset(self):
        return self.r2_freq_offset

    def set_r2_freq_offset(self, r2_freq_offset):
        self.r2_freq_offset = r2_freq_offset
        self.freq_xlating_fir_filter_xxx_0_0.set_center_freq(-1*self.r2_freq_offset)

    def get_r1_sps(self):
        return self.r1_sps

    def set_r1_sps(self, r1_sps):
        self.r1_sps = r1_sps

    def get_preamble_len(self):
        return self.preamble_len

    def set_preamble_len(self, preamble_len):
        self.preamble_len = preamble_len
        self.Zwave_preamble_0.set_preamble(self.preamble_len)

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.osmosdr_sink_0.set_center_freq(self.center_freq+self.tx_freq_offset, 0)
        self.rtlsdr_source_0.set_center_freq(self.center_freq + self.rx_freq_offset, 0)


def main(top_block_cls=top_block, options=None):

    tb = top_block_cls()
    tb.Start(True)
    tb.Wait()


if __name__ == '__main__':
    main()
