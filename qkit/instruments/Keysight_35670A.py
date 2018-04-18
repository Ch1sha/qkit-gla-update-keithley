# Agilent_VNA_E5071C driver, P. Macha, modified by M. Weides July 2013, J. Braumueller 2015
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import types
import logging
import time
import numpy as np
import math
from qkit.instruments.visa_prologix import instrument

class Keysight_35670A(instrument, Instrument): # insert Instrument
    """
    This is the python driver for the Keysight 35670A signal analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)
    
    """

    def __init__(self, name, address, reset=False, **kwargs):
        """
        Initializes 

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        """

        print 'Initializing while take some seconds... Do not worry'
        self.ip = kwargs.get("ip", "10.22.197.155")
        super(Keysight_35670A, self).__init__(address, timeout=10, chunk_size=4096, delay=0.05, ip=self.ip)
        Instrument.__init__(self, name, tags=['physical'])
        #self.calibration()

        
        # Implement parameters
        self.add_parameter('instrument_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('nop', type=types.IntType,
            flags=Instrument.FLAG_GET,
            minval=101, maxval=801)
            
        self.add_parameter('averages', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=99999)                    

        self.add_parameter('Average', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)   

        self.add_parameter('centerfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=51.2e3,
            units='Hz', tags=['sweep'])

        self.add_parameter('startfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=51.2e3,
            units='Hz', tags=['sweep'])            

        self.add_parameter('stopfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=51.2e3,
            units='Hz', tags=['sweep'])                        

        self.add_parameter('span', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=51.2e3,
            units='Hz')        
                     
        self.add_parameter('frequency_resolution', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=100, maxval=800)
        
        self.add_parameter('sweeptime', type=types.FloatType,   #JB
            flags=Instrument.FLAG_GET,
            minval=0, maxval=10000,
            units='s')
            
        self.add_parameter('sweeptime_averages', type=types.FloatType,   #JB
            flags=Instrument.FLAG_GET,
            minval=0, maxval=1e-3,
            units='s')
            
        self.add_parameter('window_type', type=types.StringType,
            flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('active_channels', type=types.StringType,
            flags=Instrument.FLAG_GETSET)
            
        self.add_parameter('repeat_averaging', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('get_single_trace')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')
        self.add_function('calibration')
        self.add_function('abort_measurement')
        self.add_function('set_measurement_continous')
        self.add_function('measure_PSD')
        self.add_function('fast_averaging')
        self.add_function('set_display_format')
        self.add_function('select_trace_format')
        #include math_function maybe
        
        if reset is True:
            self._set_GPIB_dev_reset()
            time.sleep(5)

        self.device_type='signal_analyzer'
        self.set_instrument_mode('FFT')
        self.set_return_format()
        self.get_all()

    def get_all(self):
        if self.instrument_mode is 'FFT':
            self.get_centerfreq()
            self.get_span()
            self.get_frequency_resolution()
            self.get_startfreq()
            self.get_stopfreq()
            self.get_window_type()
        self.get_instrument_mode()
        self.get_averages()
        self.get_sweeptime()
        self.get_sweeptime_averages()
        self.get_active_channels()
        self.get_nop()
        self.y_unit_c1=self.get_y_unit(1)
        self.y_unit_c2=self.get_y_unit(2)


    def ready(self):
        """This is a proxy function, returning True when the signal analyzer has finished measuring / averaging."""
        if (self._read_operation_status_register() & 256) is 0:
            return True
        else:
            return False

    def set_return_format(self, s_digits=3):
        '''specifies the number of significant digits'''
        self.write('FORMAT:DATA ASCii, {}'.format(s_digits))
    
    def calibration(self):
        reply=self.ask('*cal?')
        if reply is not 0:
            print "calibration error!"

    def auto_calibration(self, status):
        self.write('calibration:auto {}'.format(status))

    def abort_measurement(self):
        self.write('abor')

    def start_measurement(self):
        """starts a new measurement"""
        self.write("INIT:IMM")

    def set_measurement_continous(self, pause):
        """pauses(=0) or resumes(=1) the measurement"""
        self.write("INIT:CONT {}".format(pause))

    def _read_operation_status_register(self):
        """reads the operation status register, returns??"""
        return int(self.ask("STAT:OPER:COND?")[1:-1])

    def pre_measurement(self):
        self.get_all()

    def post_measurement(self):
        """nothing to do here??"""
        pass

    def do_set_active_channels(self, channel):
        """
        activates the chosen channel(s), not sure how it really works
        expects string 'A','B','AB' for channel 1, 2, 1+2
        """
        self.write("CALC:ACT "+channel)

    def do_get_active_channels(self):
        """gets the active channels A,B,AB for channel 1,2,1+2"""
        return self.ask('CALC:ACT?')[:-1]

    def set_input_channels(self, channels, status):
        """ don't know if needed. expects channel as an array and status as 0 or 1"""
        if status is 0 and 1 in channels:
            print "channel 1 must always be on"
            return
        state=['OFF', 'ON' ]
        for i in channels:
            self.write(':inp{} {}'.format(i, state[status]))

    #### Frequency options ####

    def do_set_centerfreq(self, center_freq): # in Hz
        """sets the center frequency"""
        self.write("Freq:Cent {}".format(center_freq))

    def do_get_centerfreq(self):
        """gets the center frequency"""
        #print self.ask("Freq:Cent?")
        self.centerfreq=float(self.ask("Freq:Cent?")[:-1])
        return self.centerfreq

    def do_set_startfreq(self, start_freq):
        """sets the start frequency"""
        self.write("Freq:Start {}".format(start_freq))

    def do_get_startfreq(self):
        """gets the start frequency"""
        self.startfreq=float(self.ask("Freq:Start?")[:-1])
        return self.startfreq

    def do_set_span(self, span):
        """sets the frequency span"""
        self.write("Freq:Span {}".format(span))

    def do_get_span(self):
        """gets the frequency span"""
        self.frequency_span=float(self.ask("Freq:Span?")[:-1])
        return self.frequency_span

    def do_set_frequency_resolution(self, resolution):
        """sets the frequency resolution in lines (unitless)"""
        if resolution not in [100, 200, 400, 800]:
            print 'only 100, 200, 400, 800 are allowed values'
        else:
            self.write("Freq:Res {}".format(resolution))
            self._nop=resolution+1

    def do_get_frequency_resolution(self):
        """gets the frequency resolution"""
        return int(float(self.ask("Freq:Res?")[:-1]))

    def do_get_nop(self):
        """proxy function for spectroscopy script"""
        if self.instrument_mode is 'FFT':
            self._nop= self.get_frequency_resolution()+1
        if self.instrument_mode is 'histogram':
            self._nop = 1 # for pseudo_vna_scan with spectroscopy scrpit
        return self._nop

    def do_set_stopfreq(self, stop):
        """sets the stop frequency"""
        self.write("Freq:Stop {}".format(stop))

    def do_get_stopfreq(self):
        """gets the stop frequeny"""
        self.stopfreq=float(self.ask("Freq:Stop?")[:-1])
        return self.stopfreq

    ### time trace options ###

    def set_frequency_bins():
        '''sets frequency bin in histogram mode'''
        self.write("")


    '''def set_measurement_time'''


    def do_set_instrument_mode(self, mode):
        """sets the instrument mode, expects string: 'FFT', 'histogram', 'correlation' """
        if mode is 'FFT':
            mode_number = 0
        elif mode is 'histogram':
            mode_number = 4
        elif mode is 'correlation':
            mode_number = 5
        else:
            print 'wrong input'
            return
        self.instrument_mode = mode
        self.write('INST:NSEL {}'.format(mode_number))


    def do_get_instrument_mode(self):
        """returns the instrument mode"""
        mode_number=int(self.ask('INST:NSEL?')[1:-1])
        if mode_number is 0:
            self.instrument_mode = 'FFT'
        elif mode_number is 4:
            self.instrument_mode = 'histogram'
        elif mode_number is 5:
            self.instrument_mode = 'correlation'
        return self.instrument_mode


    def do_set_sweep_mode(self, mode):
        """sets sweepmode to mode='AUTO' or 'MAN' """
        if mode not in ['AUTO', 'MAN']:
            print 'wrong input only AUTO and MAN are valid'
        else:
            self.write('swe:mode '+mode)

    def do_set_sweeptime(self, time):
        """sets the sweep time (recording time) in sec  sweeptime=freqspan/freqresolution. Chaning either will change the other"""
        self.write('swe:TIME {}'.format(time))

    def do_get_sweeptime(self):
        """gets the sweep time (recording time) """
        self.sweeptime=float(self.ask('swe:TIME?')[:-1])
        return self.sweeptime

    def do_get_sweeptime_averages(self):
        self.sweeptime_averages = self.get_sweeptime()*self.get_averages()
        return self.sweeptime_averages

    def do_set_window_type(self, type):
        """sets the window type, expects string either 'HANN', 'FLAT' or 'UNIF' """
        if type not in ['HANN', 'FLAT', 'UNIF']:
            print "wrong input only HANN, FLAT, UNIF are allowed"
        else:
            self.write('WINDOW '+type)

    def do_get_window_type(self):
        """gets the window type"""
        self.window_type = self.ask('WINDOW?')[:-1]
        return self.window_type

    def set_autoscale(self, trace, option):
        """turns autoscalle off and on. A trace has to be selected, option must be a string [AUTO, OFF, ON, ONCE] or 0 and 1"""
        self.write('disp:wind{}trac:y:auto '.format(trace)+option)

    def set_input_shielding(mode, channel = [1,2]):
        """ determines the input shielding mode (expects string), either "ground" or "floating", for the chosen channels"""
        for i in channel:
            self.write('INP{}:LOW '.format(i)+mode)

    def set_input_shielding(channel):
        """ returns the input shielding mode of the chosen channel"""
        return self.ask('INP{}:LOW?'.format(i))[:-1]

    def set_range(self, channel, value):
        """sets a fixed autorange, expects channel as list and an input value in Volts and converts it to dBV"""
        dbV=20*np.log(value)
        for i in channel:
            self.write('SENS:VOLT{}:DC:RANGE {}'.format(i, value))

    def set_autorange(self, mode, channel = [1,2]):
        """turns (1) on or off (0) the range of the chosen channel to auto"""
        for i in channel:
            self.write('sens:volt{}:dc:range:auto {}'.format(i, mode))

    def set_display_format(self, number):
        """selects the number of traces to be displayed"""
        option={1: 'SINGLE', 2: 'ULOWER', 4:'QUAD'}
        self.write('DISPLAY:FORM ' + option[number])

    def select_trace_format(self, trace, option):
        """selects the display format for the specified trace, i.e., linear, phase, real, imag, NYQuist, UPHase, GDElay, POLAR"""
        self.write('calc{}:format {}'.format(trace, option))

    ########## AVERAGING ##############

    def do_set_Average(self, status):
        """turns averagin off/on"""
        if status not in [0,1]:
            print "wrong input 0=off, 1=on"
        else:
            self.set_measurement_continous(0) # pauses measurement so that new sequence does not start automatically
            self.write('AVER {}'.format(int(status)))

    def do_get_Average(self):
        return bool(self.ask('AVER?')[1:-1])

    def fast_averaging(self, status, displaynumber=None):
        """turns on fast averaging, i.e., display is only updated at the chosen displaynumber"""
        if status not in [0,1]:
            print "wrong input 0=off, 1=on"
            return
        if status is 1:
            self.write('AVERAGE:IRES:RATE {}'.format(displaynumber))
            self.write('Average:IRES:Stat {}'.format(status))
        else:
            self.write('Average:Ires:Stat {}'.format(status))

    def do_set_averages(self, number):
        """sets the number of averages"""
        self.write('AVER:COUN {}'.format(number))

    def do_get_averages(self):
        """gets the numbers of averages"""
        if self.instrument_mode is 'histogram':
            self.averages=1
        else:
            self.averages=int(float(self.ask('AVER:COUN?')[:-1]))
        return self.averages

    def do_set_repeat_averaging(self, status):
        """specify what happens after average_number is reached, i.e., repeat measurements or wait"""
        if status is 0:
            self.write('AVERAGE:TCON FREEZE')
        elif status is 1:
            self.write('AVERAGE:TCON REPEAT')
        else:
            print "wrong input 0=HOLD, 1=REPEAT"

    def do_get_repeat_averaging(self):
        repeat_aver=self.ask('AVER:TCON?')[:-1]
        if repeat_aver is 'FRE':
            return False
        if repeat_aver[:3] is 'REP':
            return True

   ########## MATH-OPTIONS #########

    def math_expression(self, register, expression):
        """stores a math expression (string conform with the device options) into the chosen register"""
        self.write('Calculate:Math:Expr{} '.format(register) + expression)

    def math_state(self, channel, status):
        """activates math evalution for chosen schannel"""
        self.write('calculate{}:math:state {}'.format(channel, status))

    def math_select(self, channel, register):
        """selects a previously defined math_expression in a register for a channel"""
        self.write(':calc{}:math:select F{}'.format(channel, register))

    def calculate_PSD(self, channel):
        """Calculates and display the PSD for the chosen channel"""
        expression='(PSD(PSPEC{}))'.format(channel)
        self.math_expression(channel, expression)
        self.math_state(channel, 1)
        self.math_select(channel, channel)

    ######## Getting the data ######

    def get_freqpoints(self):
        """returns the x_values of a trace as numpy-array"""
        if self.instrument_mode is 'FFT':
            self.set_averages(1)
            self.start_measurement() # device only sets new x-axis when new measurement has ended
            while not self.ready(): # but spectroscopy asks for x-values before meausurment is started
                pass
            self.set_averages(self.averages)
            self.x_values=np.fromstring(self.ask("CALC:X:DATA?"), dtype=np.float, sep=',')
            return self.x_values[0:self.get_nop()]
        if self.instrument_mode is 'histogram':
            self.start_measurement() # device only sets new x-axis when new measurement has ended
            while not self.ready(): # but spectroscopy asks for x-values before meausurment is started
                pass
            self.x_values = np.fromstring(self.ask("CALC:X:DATA?"), dtype=np.float, sep=',')
            return self.x_values
        else:
            self.x_values=np.fromstring(self.ask("CALC:X:DATA?"), dtype=np.float, sep=',')
            return self.x_values

    def get_single_trace(self, channel):
        """returns the trace of channel 1 or 2"""
        trace_values=np.fromstring(self.ask("CALC{}:DATA?".format(channel)), dtype=np.float, sep=',')
        return trace_values

    def get_tracedata(self, type='AmpPha'):
        I=self.get_single_trace(1)
        Q=self.get_single_trace(2)
        if self.instrument_mode is 'FFT':
            if type is 'RealImag':
                return I,Q
            else:
                amp = np.absolute(I + 1j * Q)
                pha = np.angle(I + 1j * Q)
                return amp, pha

        else: # in histogram mode for pseudo vna scan, return only max value
            I_max=(self.x_values[np.argmax(I)])
            Q_max=(self.x_values[np.argmax(Q)])
            amp = np.absolute(I_max + 1j * Q_max)
            pha = np.angle(I_max + 1j * Q_max)
            if type is 'RealImag':
                return [I_max], [Q_max]
            elif type is 'AmpPha':
                return [amp], [pha]
            elif type is 'both':
                return [amp],[pha],[I_max],[Q_max]

    def get_tracedata_2d(self):
        I_real=self.get_single_trace(1)
        Q_real=self.get_single_trace(2)
        I_imag=self.get_single_trace(3)
        Q_imag=self.get_single_trace(4)
        return I_real, I_imag, Q_real, Q_imag


    def set_y_unit(self, unit, channel):
        """sets the y-unit (string), can also be used for PSD calucalation"""
        #unit = r"'"+unit+r"'"
        if channel in [1,2,3,4]: # implement string for unit
            self.write("calculate{}:unit:voltage ".format(channel)+ unit) 

    def get_y_unit(self, channel):
        """gets the y-unit"""
        if channel in [1,2,3,4]:
            y_unit=self.ask('CALCulate{}:UNIT:VOLTage?'.format(channel))[:-1]
            return y_unit.strip('"')
        else:
            print 'wrong input'

    def measure_PSD(self, channel):
        """proxy funciton for set y-unit with unit = "V2/Hz" """
        self.set_y_unit('V2/HZ', channel)
