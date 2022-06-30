# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM]
# description of function: this class acts to control the SPIMMM.

# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# serial is used for communication with the hardware
import serial
import re
import time
import random
import numpy as np
import threading


#####################################################################################################################
#####################################################################################################################

class SPIMMM:

    def __init__(self):
        # perform all the necessary actions for setting up
        # connect the serial ports, set up the arduino, stage and laser

        self.open_ports()
        # clear the startup string received from the arduino
        self.ard.readline()
        self.sendcfg()
        self.get_pos()
        self.laser_power()

    ################################################################################################################
    # Variables and objects ##########################

    # variables ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    dbg = False

    # small move time in milliseconds; the time taken to make a small move on the stage,
    # which is measured manually from the PI step response tool
    smt = 20

    # time between frames in milliseconds
    frt = 25

    # camera exposure time in milliseconds
    exp = 10

    # temperature control board response
    tcr = ''

    # heater mode; 0 off, 1 cool, 2 heat
    htm = 0

    # heater power; 0-799
    hpw = 0

    # fan mode; 0 off, 1 on
    fnm = 0

    # temperature setpoint in degrees C
    tem = 17

    # measured temperature in degrees C
    tempm = 20.0

    # the period of the control loop in seconds
    ttc = 1

    # proportional control constant for the temperature control module (heating mode)
    tkp = 120

    # proportional control constant for the temperature control module (cooling mode)
    tkpc = 600

    # integral control constant for the temperature control module
    tki = 1.5

    # total error for the heater controller
    ers = 0

    # boolean value indicating if the temperature controller is on target
    ont = False

    # engage temperature step mode
    tst = False

    # the logging period for temperature logging
    lgp = 1

    # the polling period for temperature polling
    plp = 0.1

    # slope parameter of stage distance to mirror DAC count relation
    slp = -4468.4

    setpos = 5.6

    # offset parameter of stage distance to mirror DAC count relation
    off = 4095 - int(setpos * slp)

    # starting position of the stage as used for volume imaging in mm
    stp = 6.0

    # the distance travelled by the stage in a small move as used for volume imaging, in mm
    dst = 0.002

    # number of steps  used for volume imaging
    frn = 5

    # the stage position in mm
    pos = 0.0

    # boolean declaring stage engaged
    eng = False

    # number of volumes
    vln = 41

    # time between volumes in millis
    vlt = 1000

    # the 488nm laser power in Watts
    pwr1 = 0.010

    # the 561nm laser power in Watts
    pwr2 = 0.010

    # the 488nm laser state on or off
    lst1 = False

    # the 561nm laser state on or off
    lst2 = False

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # serial objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # arduino COM port; the COM port that the OS assigns to the arduino,
    # which runs the mirror and camera triggering software
    ard = serial.Serial()
    ard.baudrate = 115200
    ard.timeout = 5
    ard.port = 'COM3'

    # 488nm laser COM port; the COM port that the OS assigns to the coherent laser
    las1 = serial.Serial()
    las1.baudrate = 9600
    las1.timeout = 5
    las1.port = 'COM8'

    # 561nm laser COM port; the COM port that the OS assigns to the coherent laser
    las2 = serial.Serial()
    las2.baudrate = 9600
    las2.timeout = 5
    las2.port = 'COM7'

    # threading objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    seriallock = threading.Lock()

    data_in = threading.Event()

    # signals to the thread that runs the temperature controller
    tempcont = threading.Thread()

    tempcont_halt = threading.Event()

    # signals to the thread that runs the heater board poll
    temppoll = threading.Thread()

    temppoll_halt = threading.Event()

    # signals to the thread that runs the temperature logger
    templog = threading.Thread()

    templog_halt = threading.Event()

    ################################################################################################################
    # Arduino config functions COM3 COM7 COM8 ##########################

    # open the COM ports for communication with the hardware
    def open_ports(self):
        if not self.ard.isOpen():
            try:
                # readline blocks further execution until the port is connected and the arduino responds
                self.ard.open()
                # print('arduino connected')
            except serial.SerialException:
                raise UserWarning('could not connect to arduino')

        if not self.las1.isOpen():
            try:
                self.las1.open()
                # print('488nm laser connected')
            except serial.SerialException:
                print('could not connect to 488nm laser')

        if not self.las2.isOpen():
            try:
                self.las2.open()
                # print('561nm laser connected')
            except serial.SerialException:
                print('could not connect to 561nm laser')

    # close ports opened by 'open_ports'
    def close_ports(self):
        self.ard.close()
        self.las1.close()
        self.las2.close()

    # send and read configuration parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # sends configuration variables to the arduino for running a volume
    def sendcfg(self):
        self.seriallock.acquire()
        self.ard.write(
            'SET {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} \r'.format(
                str(self.htm),
                str(self.hpw),
                str(self.fnm),
                str(self.frn),
                str(self.frt),
                str(self.exp),
                str(self.stp),
                str(self.dst),
                str(self.slp),
                str(self.off)))
        self.seriallock.release()

    # reads configuration variables from the arduino
    def readcfg(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('REP\r')
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        print(self.ard.readline())
        self.seriallock.release()

    ################################################################################################################
    # Laser functions COM7 COM8 ##########################

    # set laser power and update state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # sets the laser power according to the level set in cfg.pwr1 and cfg.pwr2 and sets the lasers on or off
    def laser_power(self):
        # the Coherent laser only takes arguments up to the nearest mW,
        # this will also cause an error if anything but a number comes in
        if self.las1.isOpen():
            try:
                if self.pwr1 > 0.0:
                    power1 = round(self.pwr1, 3)
                    self.las1.write('SOUR:AM:INT\r')
                    self.las1.write('SOUR:POW:LEV:IMM:AMPL ' + str(power1) + ' \r')
                    if self.dbg:
                        print('488nm laser set to ' + str(power1 * 1000) + 'mW')
                else:
                    print('488nm laser power must be positive')
            except TypeError:
                print('488nm laser power set incorrectly')
            if self.lst1:
                self.las1.write('SOUR:AM:STAT ON\r')
            else:
                self.las1.write('SOUR:AM:STAT OFF\r')
        else:
            print('power setting failed: 488nm laser not connected')

        if self.las2.isOpen():
            try:
                if self.pwr2 > 0.0:
                    power2 = round(self.pwr2, 3)
                    self.las2.write('SOUR:AM:INT\r')
                    self.las2.write('SOUR:POW:LEV:IMM:AMPL ' + str(power2) + ' \r')
                    if self.dbg:
                        print('561nm laser set to ' + str(power2 * 1000) + 'mW')
                else:
                    print('561nm laser power must be positive')
            except TypeError:
                print('561nm laser power set incorrectly')
            if self.lst2:
                self.las2.write('SOUR:AM:STAT ON\r')
            else:
                self.las2.write('SOUR:AM:STAT OFF\r')
        else:
            print('power setting failed: 561nm laser not connected')

    def laser_shutdown(self):

        if self.las1.isOpen():
            self.las1.write('SOUR:AM:STAT OFF\r')
            self.lst1 = False
            self.las1.close()
        else:
            print('488nm laser already disconnected')

        if self.las2.isOpen():
            self.las2.write('SOUR:AM:STAT OFF\r')
            self.lst2 = False
            self.las2.close()
        else:
            print('561nm laser already disconnected')

    ################################################################################################################
    # Stage & Mirror functions  Microcontroller COM3 ##########################

    # move stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # takes a position between -6.5 and 6.5 and translates the stage to that position by communicating with the arduino
    def stage(self, position):
        # the PI stage only takes arguments up to the nearest nanometer,
        # this will also cause an error if anything but a number comes in
        # NOTE: for moves >10um, this operation takes at least 2.5s
        try:
            position = round(position, 6)
            if abs(position) > 6.495:
                print('warning: position out of bounds')
                return
            distance = abs(position - self.pos)
            self.pos = position
            # if the distance is over 20 microns, move slowly, otherwise move fast
            self.seriallock.acquire()
            if distance > 0.200:
                self.ard.write('STS ' + str(self.pos) + '\r')
            else:
                self.ard.write('STA ' + str(self.pos) + '\r')
            self.seriallock.release()
        except TypeError:
            print('error: position value not a float')

    # get stage position ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_pos(self):
        # return the position of the PI stage in mm
        self.seriallock.acquire()
        self.ard.write('QRP\r')
        self.seriallock.release()
        resp = self.ard.readline()
        try:
            self.pos = float(resp)
        except Exception:
            raise SystemExit("Stage Disconnected")

    # halt stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # halts the stage by communicating with the arduino
    def hlt(self):
        # trigger the halt command on the PI stage
        self.seriallock.acquire()
        self.ard.write('STP ' + '\r')
        self.seriallock.release()

    # reboot stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # reboots the stage by communicating with the arduino
    def rbt(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('RBT ' + '\r')
        self.seriallock.release()
        self.eng = True

    # engage stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # engages the stage by communicating with the arduino
    def engage(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('ENG ' + '\r')
        self.seriallock.release()
        self.pos = 0.0
        self.eng = True

    # disengage stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # disengages the stage by communicating with the arduino
    def disengage(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('DNG ' + '\r')
        self.seriallock.release()
        self.eng = False

    # extrapolate conservative estimate of large stage movement time ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # takes the stage distance to move and returns the time to wait for it to complete, based on the small move time
    def pau(self, stage_move):
        pause = self.smt * (stage_move / self.dst)
        pause = round(pause, 6)
        return pause

    # reset error state from the stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def err(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('ERR\r')
        resp = self.ard.readline()
        resp = resp + self.ard.readline()
        self.seriallock.release()
        return resp

    # compute mirror count for focus ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def mirror_count(self, stage_dist):
        # linear relationship between mirror voltage and high of lightsheet
        mirror_cnt = int((stage_dist * self.slp) + self.off)  # self.slp is negative
        # 4095 is DAC max voltage = 2.3V, set for stage_dist < 5.6mm
        if mirror_cnt > 4095:
            mirror_cnt = 4095
            print('warning: mirror out of range')
        # 0 is DAC min voltage = 0.2V, set for stage_dist > 6.5mm
        if mirror_cnt < 0:
            mirror_cnt = 0
            print('warning: mirror out of range')
        return mirror_cnt

    # move mirror ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # takes a count between 0 and 4095 and converts it into a voltage that controls the laser position
    def mirror(self, target_pos):
        # only integers are permitted,
        # this will also cause an error if anything but a number comes in

        # mirror voltage is the sum of DAC from Arduino and Supply on the desk
        # with DAC 0/2.3V and Desk's supply in -0.2/11.1V
        count = self.mirror_count(target_pos)
        try:
            # send count to Arduino'S DAC

            self.seriallock.acquire()
            self.ard.write('DAC ' + str(count) + '\r')
            self.seriallock.release()
        except ValueError:
            print('error: mirror value not an int')

    # move stage and mirror together ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # takes a position between -6.5 and 6.5 and translates the stage, keeping focus with the laser sheet
    # keep in focus between 5.7 and 6.5
    def focus(self, target_pos):
        self.mirror(target_pos)
        self.stage(target_pos)

    def read_mirror(self):
        self.seriallock.acquire()
        self.ard.write('RDM\r')
        self.seriallock.release()
        resp = self.ard.readline()
        return resp

    ################################################################################################################
    # Heater functions  Arduino COM3 ##########################

    # push heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def sdh(self):
        self.seriallock.acquire()
        self.ard.write('STH\r')
        self.seriallock.release()

    # read heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def rdh(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('RDH\r')
        self.seriallock.release()
        resp = self.ard.readline()
        if 'END' in resp:
            return resp
        else:
            print('temperature poll error')
            time.sleep(0.1)
            return False

    # read heater parameters and control temperature~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def clt(self):

        # count is the number of polling periods that the bath must within +- 1 degree of the set point to be on
        # target
        # maxsig is the maximum signal that can be sent to the temperature driver board coolingfactor is the
        # proportion of maximum power that can be applied in cooling mode

        count = 100
        maxsig = 799
        coolingfactor = 0.75

        maxers = maxsig / self.tki

        # extract measured temperature from readout we may want to refactor the extraction as a function that takes a
        # keyword and a string, and returns the value of the argument after it, though given that we're dealing with
        # mixed data types, this might be more difficult than it is useful paramstring = "$HC,MODE,1,PWM,400,TEMP,
        # 26.5,END"

        paramstring = self.tcr
        kwtemp = [match.start() for match in re.finditer(re.escape('TEMP'), paramstring)]
        delimiters = [match.start() for match in re.finditer(re.escape(','), paramstring)]
        position = filter(lambda x: x >= kwtemp[0], delimiters)
        position = position[0:2]
        position[0] = position[0] + 1
        tempstring = paramstring[position[0]:position[1]]
        if "." in tempstring:
            self.tempm = float(tempstring)
        else:
            self.tempm = int(tempstring)

        # calculate the error and set the parameters
        temperror = self.tem - self.tempm

        # this block checks to see if the controller is on target by checking if the temperature has gone out of
        # range recently

        if abs(temperror) <= 1:
            count = count - 1
            if count <= 0:
                count = 1
            self.ont = True
        else:
            count = 10
            self.ont = False

        # block to prevent integrator wind-up

        if abs(temperror) < 8:
            self.ers = self.ers + (temperror * self.ttc)
        else:
            self.ers = 0

        if self.ers > maxers:
            self.ers = maxers
        elif self.ers < 0:
            self.ers = 0

        if self.tst:
            signal = 500
        elif temperror < 0:
            signal = (temperror * self.tkpc) + (self.ers * self.tki)
        else:
            signal = (temperror * self.tkp) + (self.ers * self.tki)

        if signal > maxsig:
            signal = maxsig
        elif signal < -(maxsig * coolingfactor):
            signal = -(maxsig * coolingfactor)

        self.hpw = abs(signal)

        if signal >= 0:
            self.htm = 2
            self.fnm = 0

        else:
            self.htm = 1
            self.fnm = 1

        if self.dbg:
            print('demand temperature: ' + str(self.tem) + ', ' + 'measured temperature: ' + str(self.tempm))
            print('proportional signal: ' + str(temperror * self.tkp) + ', ' + 'integral signal: '
                  + str((self.ers * self.tki)))
            print('signal: ' + str(signal) + ', ' + 'heater power: ' + str(self.hpw) + ', ' + 'heater mode: ' + str(
                self.htm))
            if self.ont:
                print('on target')

        # set the peltier duty cycle and throttle down to the maximum set above

        # send the parameters and push to the heater
        self.sendcfg()
        self.sdh()

    # run temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # not to be used directly, this function instructs the temperature control module to set the temperature
    def acttempcont(self):
        if not self.temppoll.isAlive():
            self.starttemppoll()

        while not self.temppoll.isAlive() and self.data_in.isSet():
            print('waiting for temperature controller')
            time.sleep(0.5)

        # print('temperature controller running')
        self.tempcont_halt.clear()
        while not self.tempcont_halt.isSet():
            if self.data_in.isSet():
                self.clt()
            time.sleep(self.ttc)

    # starts a thread that runs simple temperature control from acttempcont
    def starttempcont(self):
        if self.tempcont.isAlive():
            print('warning: thread already running')
        else:
            self.ers = 0
            self.tempcont = threading.Thread(name='tempcont', target=self.acttempcont)
            self.tempcont.start()

    def halttempcont(self):
        if not self.tempcont.isAlive():
            print('warning: temperature control not running')
        else:
            if not self.tempcont_halt.isSet():
                self.tempcont_halt.set()
                # print('temperature control halted')
            else:
                print('warning: flag not set')

        # shut the heater controller down
        self.htm = 0
        self.fnm = 0
        self.sendcfg()
        self.sdh()
        self.temppoll_halt.set()

    # run temperature logging ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # not to be used directly, this function reads the temperature control module and logs the parameters
    def acttemplog(self):
        if not self.temppoll.isAlive():
            self.starttemppoll()

        while not self.data_in.isSet():
            print('waiting for temperature controller')
            time.sleep(0.1)

        print('temperature logging running')
        timestr = time.strftime('%Y%m%d-%H%M%S')
        contstring = 'Kp' + '_' + str(self.tkp) + '_' + 'Ki' + '_' + str(self.tki)
        templogname = 'templog_' + timestr + '_' + contstring + '.csv'
        templogname = 'templog/' + templogname
        templogfile = open(templogname, 'a')
        templogfile.write('Device,,Mode,,PWM,,Temp,,\n')

        self.templog_halt.clear()
        while not self.templog_halt.isSet():
            templogfile.write(self.tcr.rstrip() + ',' + 'SET TEMP' + ',' + str(self.tem) + ',' + 'SYS TIME' + ','
                              + str(time.time()) + '\n')
            time.sleep(self.lgp)
        templogfile.close()

    # starts a thread that logs the temperature control parameters to a file for analysis
    def starttemplog(self):
        if self.templog.isAlive():
            print('warning: thread already running')
        else:
            templog = threading.Thread(name='templog', target=self.acttemplog)
            templog.start()

    def halttemplog(self):
        if not self.templog.isAlive():
            print('warning: temperature logging not running')
        else:
            if not self.templog_halt.isSet():
                self.templog_halt.set()
                self.temppoll_halt.set()
                print('temperature logging halted')
            else:
                print('warning: flag not set')

    # poll temperature control board ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def acttemppoll(self):
        self.data_in.clear()
        if not self.ard.isOpen():
            print('warning: port is not open')
            print('attempting to open')
            try:
                self.open_ports()
                print('ports opened successfully')
            except UserWarning:
                print('ports unreachable, releasing thread locks in 2 seconds')
                time.sleep(2)
                self.seriallock.release()
                return

        self.temppoll_halt.clear()
        while not self.temppoll_halt.isSet():
            read = self.rdh()
            if read:
                self.tcr = read
                self.data_in.set()
            else:
                self.data_in.clear()
            time.sleep(self.plp)

    def starttemppoll(self):
        if self.temppoll.isAlive():
            print('warning: thread already running')
        else:
            self.temppoll = threading.Thread(name='temppoll', target=self.acttemppoll)

            self.temppoll.start()

    def halttemppoll(self):
        if not self.temppoll.isAlive():
            print('warning: temperature polling not running')
        else:
            if not self.temppoll_halt.isSet():
                self.temppoll_halt.set()
                print('temperature polling halted')
            else:
                print('warning: flag not set')

    ################################################################################################################
    # Magnet functions Arduino COM4 ##########################

    def open_controller(self):
        try:
            ps = serial.Serial('COM4', 19200, timeout=0.05)
            # print('Connection to Current Controller Successful')
            return ps
        except serial.SerialException:
            print('Error: Could not connect to Current Controller')

    def close_controller(self, connection_object):
        connection_object.close()

    def write_values(self, connection_object, config, amplitude):
        supply = range(1, 5)
        random.shuffle(supply)

        current_configs = np.array([[0, 1, 1, 0],
                                    [0.5, 0.5, 1, 1],
                                    [1, 1, 0.5, 0.5],
                                    [1, 0, 0, 1]])

        current_values = amplitude * current_configs[config]
        current_values[current_values == 0] = 0.001

        self.seriallock.acquire()
        for i in supply:
            connection_object.write('PW ' + str(i) + ' ' + str(current_values[i - 1]) + '\r\n')
            time.sleep(0.02)
        self.seriallock.release()

    def switch_on(self, connection_object):
        self.seriallock.acquire()
        connection_object.write('P_ON\r\n')
        self.seriallock.release()

    def switch_off(self, connection_object):
        self.seriallock.acquire()
        connection_object.write('P_OFF\r\n')
        self.seriallock.release()

    def trigger_magnet(self, duration, conf, amp):
        connection_object = self.open_controller()
        time.sleep(1)
        self.write_values(connection_object, conf, amp)
        time.sleep(0.02)
        self.switch_on(connection_object)
        time.sleep(duration)
        self.switch_off(connection_object)
        time.sleep(0.02)
        self.close_controller(connection_object)

    def start_magnet(self, conf, amp):
        connection_object = self.open_controller()
        time.sleep(1)
        self.write_values(connection_object, conf, amp)
        time.sleep(0.02)
        self.switch_on(connection_object)
        time.sleep(0.02)
        self.close_controller(connection_object)

    def stop_magnet(self):
        connection_object = self.open_controller()
        time.sleep(1)
        self.switch_off(connection_object)
        time.sleep(0.02)
        self.close_controller(connection_object)

    ################################################################################################################
    # Volume capture functions COM3 ##########################

    # configure arduino to take a single volume
    def take_volume_cfg(self, frn, frt, exp, stp, dst):
        self.frt = frt
        self.exp = exp
        self.stp = stp
        self.dst = dst
        self.frn = frn
        self.sendcfg()
        # self.readcfg()

    # take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def take_volume(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('RUN\r')
        self.seriallock.release()
        resp = self.ard.readline()
        # if 'VOL' in resp:
        #     # print('Volume capture successfully ended')
        #     return True
        # else:
        #     print('Error during volume capture')
        #     return False
        # while 'VOL' not in resp:
        #     print("sliced %s/%i" % (resp.rstrip(), number_steps))
        #     resp = self.ard.readline()
        # print('Volume capture successfully ended')
        # return True
