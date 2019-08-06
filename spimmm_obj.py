# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM]
# description of function: this class acts to control the SPIMMM.

# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# serial is used for communication with the hardware

import serial
import re
import time
import threading


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# description of parameters
#
# constants~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# smt - small move time in milliseconds; the time taken to make a small move on the stage,
# which is measured manually from the PI step response tool
#
# frt - time between frames in milliseconds
#
# exp - camera exposure time in milliseconds
#
# tcr - temperature control board response
#
# htm - heater mode; 0 off, 1 cool, 2 heat
#
# hpw - heater power; 0-799
#
# fnm - fan mode; 0 off, 1 on
#
# tem - temperature setpoint in degrees C
#
# ttc - the period of the control loop in seconds
#
# tkp - proportional control constant for the temperature control module (heating mode)
#
# tkpc - proportional control constant for the temperature control module (cooling mode)
#
# tki - integral control constant for the temperature control module
#
# tst - engage temperature step mode
#
# lgp - the logging period for temperature logging
#
# plp - the polling period for temperature polling
#
# slp - slope parameter of stage distance to mirror DAC count relation
#
# off - offset parameter of stage distance to mirror DAC count relation
#
# dup - upper distance limit of stage in mm
#
# dlo - lower distance limit of stage in mm
#
# ste - the distance travelled by the stage in a small move as used for volume imaging, in mm
#
# pos - the stage position in mm
#
# imt - imaging time in seconds
#
# vrt - time between volumes in seconds
#
# pwr1 - the 488nm laser power in Watts
#
# pwr2 - the 561nm laser power in Watts
#
# lst1 - the 488nm laser state on or off
#
# lst2 - the 561nm laser state on or off
#
#
# serial objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# ard - arduino COM port; the COM port that the OS assigns to the arduino,
# which runs the mirror and camera triggering software
#
# las1 - 488nm laser COM port; the COM port that the OS assigns to the coherent laser
#
# las2 - 561nm laser COM port; the COM port that the OS assigns to the coherent laser
#
# threading objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# volume_halt - signals to the thread that runs the hardware when a volume is taken
#
# camera_halt - signals to the thread that runs the camera
#
# tempcont - signals to the thread that runs the temperature controller
#
# templog - signals to the thread that runs the temperature logger
#
# temppoll - signals to the thread that runs the heater board poll
#
# functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# open_ports - open the COM ports for communication with the hardware
#
# close_ports - close ports opened by 'open_ports'
#
# setcal - allows user input to set the mirror/stage calibration variables
#
# sendcfg - sends configuration variables to the arduino for running a volume
#
# readcfg - reads configuration variables from the arduino
#
# laser_power - sets the laser power according to the level set in cfg.pwr1 and cfg.pwr2 and sets the lasers on or off
#
# mirror - takes a count between 0 and 1023 and converts it into a voltage that controls the laser position
#
# stage - takes a position between -6.5 and 6.5 and translates the stage to that position by communicating with the
# arduino
#
# rbt - reboots the stage by communicating with the arduino
#
# hlt - halts the stage by communicating with the arduino
#
# frame - takes an exposure time in ms and commands the camera to take a frame by communicating with the arduino
#
# focus - takes a position between -6.5 and 6.5 and translates the stage, keeping focus with the laser sheet
#
# stm - takes the stage position and returns the required mirror position according to the calibration parameters
#
# pau - takes the stage distance to move and returns the time to wait for it to complete, based on the small move time
#
# tkv - command the microscope to take a volume from the arduino
#
# err - reset the error on the stage driver
#
# sdh - push the heater parameters to the heater
#
# rdh - read the heater parameters from the heater
#
# clt - control the temperature
#
# actcam - not to be used directly, this is a function that runs the camera hardware
#
# startcam - starts a thread that runs 'actcam', which will run until 'haltcam' is called
#
# haltcam - halts the thread that runs 'actcam'
#
# actvol - not to be used directly, this function instructs the hardware to take a volume on repeat
#
# startvol - starts a thread that runs 'actvol' which will run until 'haltvol' is called
#
# haltvol - halts the thread that runs 'actvol'
#
# voltime - starts a thread that runs 'actvol' which will run for a period of time defined in cfg.imt
#
# acttempcont - not to be used directly, this function instructs the temperature control module to set the temperature
#
# tempcont - starts a thread that runs simple temperature control from acttempcont
#
# actemplog - not to be used directly, this function reads the temperature control module and logs the parameters
#
# templog - starts a thread that logs the temperature control parameters to a file for analysis

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SPIMMM:

    def __init__(self):
        # perform all the necessary actions for setting up
        # connect the serial ports, set up the arduino, stage and laser

        self.open_ports()
        # clear the startup string received from the arduino
        self.ard.readline()
        self.sendcfg()
        self.laser_power()

# variables ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    dbg = True

    smt = 20

    frt = 50

    exp = 1

    tcr = ''

    htm = 0

    hpw = 0

    fnm = 0

    tem = 17

    ttc = 1

    tkp = 120

    tkpc = 600

    tki = 1.5

    tst = False

    lgp = 1

    plp = 0.1

    slp = -2222

    off = 0

    dup = 6.4

    dlo = 5.9

    ste = 0.005

    pos = 0.0

    imt = 30

    vrt = 0.5

    pwr1 = 0.010

    pwr2 = 0.010

    lst1 = False

    lst2 = False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# serial objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    ard = serial.Serial()
    ard.baudrate = 115200
    ard.timeout = 5
    ard.port = 'COM6'

    las1 = serial.Serial()
    las1.baudrate = 9600
    las1.timeout = 5
    las1.port = 'COM42'

    las2 = serial.Serial()
    las2.baudrate = 9600
    las2.timeout = 5
    las2.port = 'COM41'

# threading objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    camera_halt = threading.Event()

    volume_halt = threading.Event()

    tempcont_halt = threading.Event()

    templog_halt = threading.Event()

    temppoll_halt = threading.Event()

    test_halt = threading.Event()

    data_in = threading.Event()

    camera = threading.Thread()

    volume = threading.Thread()

    tempcont = threading.Thread()

    templog = threading.Thread()

    temppoll = threading.Thread()

    test = threading.Thread()

    seriallock = threading.Lock()

# functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_ports(self):
        if not self.ard.isOpen():
            try:
                # readline blocks further execution until the port is connected and the arduino responds
                self.ard.open()
                print('arduino connected')
            except serial.SerialException:
                raise UserWarning('could not connect to arduino')

        if not self.las1.isOpen():
            try:
                self.las1.open()
                print('488nm laser connected')
            except serial.SerialException:
                print('could not connect to 488nm laser')

        if not self.las2.isOpen():
            try:
                self.las2.open()
                print('561nm laser connected')
            except serial.SerialException:
                print('could not connect to 561nm laser')

    def close_ports(self):
        self.ard.close()
        self.las1.close()
        self.las2.close()

# send and read configuration parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def sendcfg(self):
        self.ard.write('SET ' + str(self.smt) + ' ' + str(self.frt) + ' ' + str(self.exp) + ' ' + str(self.htm) + ' '
                       + str(self.hpw) + ' ' + str(self.fnm) + ' ' + str(self.slp) + ' ' + str(self.off) + ' '
                       + str(self.dup) + ' ' + str(self.dlo) + ' ' + str(self.ste) + '\r')

    def readcfg(self):
        self.ard.flushInput()
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

# set laser power and update state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def laser_power(self):
        # the Coherent laser only takes arguments up to the nearest mW,
        # this will also cause an error if anything but a number comes in
        if self.las1.isOpen():
            try:
                power1 = round(self.pwr1, 3)
                self.las1.write('SOUR:POW:LEV:IMM:AMPL ' + str(power1) + ' \r')
            except TypeError:
                print('488nm laser power set incorrectly')
            if self.lst1:
                self.las1.write('SOUR:AM:STAT ON\r')
            else:
                self.las1.write('SOUR:AM:STAT OFF\r')
        else:
            print('488nm laser not connected')

        if self.las2.isOpen():
            try:
                power2 = round(self.pwr2, 3)
                self.las1.write('SOUR:POW:LEV:IMM:AMPL ' + str(power2) + ' \r')
            except TypeError:
                print('561nm laser power set incorrectly')
            if self.lst2:
                self.las2.write('SOUR:AM:STAT ON\r')
            else:
                self.las2.write('SOUR:AM:STAT OFF\r')
        else:
            print('561nm laser not connected')

# move mirror ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def mirror(self, count):
        # only integers are permitted,
        # this will also cause an error if anything but a number comes in
        try:
            count = int(count)
            self.ard.write('DAC ' + str(count) + '\r')
        except ValueError:
            print('mirror value set incorrectly')


# move stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def stage(self, position):
        # the PI stage only takes arguments up to the nearest nanometer,
        # this will also cause an error if anything but a number comes in
        try:
            position = round(position, 6)
            self.ard.write('STA ' + str(position) + '\r')
        except TypeError:
            print('stage value set incorrectly')

# halt stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def hlt(self):
        # trigger the halt command on the PI stage
        self.ard.write('STP ' + '\r')

# reboot stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def rbt(self):
        # trigger the reboot command on the PI stage
        self.ard.write('RBT ' + '\r')

# take frame ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def frame(self, length):
        # only integers are permitted, this will also cause an error if anything but a number comes in
        try:
            length = int(length)
            self.ard.write('FRM ' + str(length) + '\r')
        except ValueError:
            print('frame length set incorrectly')

# move stage and mirror together ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def focus(self, location):
        self.stage(location)
        self.mirror(self.stm(location))

# calculate mirror count for focus ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def stm(self, stage_dist):
        mirror_count = (stage_dist * self.slp) + self.off

        return mirror_count

# extrapolate conservative estimate of large stage movement time ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def pau(self, stage_move):
        pause = self.smt * (stage_move / self.ste)
        pause = round(pause, 6)

        return pause

# take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def tkv(self):
        self.ard.flushInput()
        self.ard.write('RUN\r')
        resp = self.ard.readline()
        print(resp)

# reset error state from the stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def err(self):
        self.ard.write('ERR\r')

# push heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def sdh(self):
        self.ard.write('STH\r')

# read heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def rdh(self):
        self.ard.flushInput()
        self.ard.write('RDH\r')
        resp = self.ard.readline()
        if 'END' in resp:
            return resp
        else:
            print('temperature poll error')
            time.sleep(0.1)
            self.rdh()

# read heater parameters and control temperature~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def clt(self):
        global errorsum
        global ontarget

#   count is the number of polling periods that the bath must within +- 1 degree of the set point to be on target
#   maxsig is the maximum signal that can be sent to the temperature driver board
#   coolingfactor is the proportion of maximum power that can be applied in cooling mode

        count = 100
        maxsig = 799
        coolingfactor = 0.75

        maxerrorsum = maxsig / self.tki

#   extract measured temperature from readout
#   we may want to refactor the extraction as a function that takes a keyword and a string, and returns the value of the
#   argument after it, though given that we're dealing with mixed data types, this might be more difficult than it is
#   useful
#    paramstring = "$HC,MODE,1,PWM,400,TEMP,26.5,END"

        paramstring = self.tcr
        kwtemp = [match.start() for match in re.finditer(re.escape('TEMP'), paramstring)]
        delimiters = [match.start() for match in re.finditer(re.escape(','), paramstring)]
        position = filter(lambda x: x >= kwtemp[0], delimiters)
        position = position[0:2]
        position[0] = position[0] + 1
        tempstring = paramstring[position[0]:position[1]]
        if "." in tempstring:
            tempm = float(tempstring)
        else:
            tempm = int(tempstring)

        # calculate the error and set the parameters
        temperror = self.tem - tempm

# this block checks to see if the controller is on target by checking if the temperature has gone out of range recently

        if abs(temperror) <= 1:
            count = count - 1
            if count <= 0:
                count = 1
            ontarget = True
        else:
            count = 10
            ontarget = False

# block to prevent integrator wind-up

        if abs(temperror) < 8:
            errorsum = errorsum + (temperror * self.ttc)
        else:
            errorsum = 0

        if errorsum > maxerrorsum:
            errorsum = maxerrorsum
        elif errorsum < 0:
            errorsum = 0

        if self.tst:
            signal = 500
        elif temperror < 0:
            signal = (temperror * self.tkpc) + (errorsum * self.tki)
        else:
            signal = (temperror * self.tkp) + (errorsum * self.tki)

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
            print('demand temperature: ' + str(self.tem) + ', ' + 'measured temperature: ' + str(tempm))
            print('proportional signal: ' + str(temperror * self.tkp) + ', ' + 'integral signal: '
                  + str((errorsum * self.tki)))
            print('signal: ' + str(signal) + ', ' + 'heater power: ' + str(self.hpw) + ', ' + 'heater mode: ' + str(
                self.htm))
            if ontarget:
                print('on target')

# set the peltier duty cycle and throttle down to the maximum set above

        # send the parameters and push to the heater
        self.sendcfg()
        self.sdh()

# run camera ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# note that the sleep parameter includes the exposure time

def actcam(self):
    print('camera started')

    self.camera_halt.clear()
    while not self.camera_halt.isSet():
        self.seriallock.acquire()
        self.frame(self.exp)
        self.seriallock.release()
        time.sleep(self.frt - (0.001 * self.exp))


def startcam(self):
    global camera
    if camera.isAlive():
        print('warning: thread already running')
    else:
        camera = threading.Thread(name='camera', target=actcam)
        camera.start()


def haltcam(self):
    if not camera.isAlive():
        print('warning: camera not running')
    else:
        if not self.camera_halt.isSet():
            self.camera_halt.set()
            print('camera acquisition halted')
        else:
            print('warning: flag not set')


# take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def actvol(self):
    self.sendcfg()
    print('microscope running')
    self.volume_halt.clear()
    while not self.volume_halt.isSet():
        self.seriallock.acquire()
        self.tkv()
        self.seriallock.release()


def startvol(self):
    global volume
    if volume.isAlive():
        print('warning: thread already running')
    else:
        volume = threading.Thread(name='volume', target=actvol)
        volume.start()


def haltvol(self):
    if not volume.is_alive():
        print('warning: volume acquisition not running')
    else:
        if not self.volume_halt.isSet():
            self.volume_halt.set()
            print('volume acquisition halted')
        else:
            print('warning: flag not set')


# run temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttempcont(self):
    if not temppoll.isAlive():
        starttemppoll()

    while not self.data_in.isSet():
        print('waiting for data')
        time.sleep(0.1)

    print('temperature control running')
    self.tempcont_halt.clear()
    while not self.tempcont_halt.isSet():
        self.seriallock.acquire()
        self.clt()
        self.seriallock.release()
        time.sleep(self.ttc)


def starttempcont(self):
    global tempcont
    if tempcont.isAlive():
        print('warning: thread already running')
    else:
        self.errorsum = 0
        tempcont = threading.Thread(name='tempcont', target=acttempcont)
        tempcont.start()


def halttempcont(self):
    if not tempcont.isAlive():
        print('warning: temperature control not running')
    else:
        if not self.tempcont_halt.isSet():
            self.tempcont_halt.set()
            self.temppoll_halt.set()
            print('temperature control halted')
        else:
            print('warning: flag not set')

# shut the heater controller down
        self.htm = 0
        self.fnm = 0
        self.seriallock.acquire()
        self.sendcfg()
        self.sdh()
        self.seriallock.release()


# run temperature logging ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttemplog(self):
    if not temppoll.isAlive():
        starttemppoll()

    while not self.data_in.isSet():
        print('waiting for data')
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


def starttemplog():
    global templog
    if templog.isAlive():
        print('warning: thread already running')
    else:
        templog = threading.Thread(name='templog', target=acttemplog)
        templog.start()


def halttemplog(self):
    if not templog.isAlive():
        print('warning: temperature logging not running')
    else:
        if not self.templog_halt.isSet():
            self.templog_halt.set()
            self.temppoll_halt.set()
            print('temperature logging halted')
        else:
            print('warning: flag not set')


# poll temperature control board ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def acttemppoll(self):
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
        self.seriallock.acquire()
        self.tcr = self.rdh()
        self.seriallock.release()
        self.data_in.set()
        time.sleep(self.plp)
    self.data_in.clear()


def starttemppoll(self):
    global temppoll
    if temppoll.isAlive():
        print('warning: thread already running')
    else:
        self.temppoll = threading.Thread(name='temppoll', target=acttemppoll)

        self.temppoll.start()


def halttemppoll(self):
    if not temppoll.isAlive():
        print('warning: temperature polling not running')
    else:
        if not self.temppoll_halt.isSet():
            self.temppoll_halt.set()
            print('temperature polling halted')
        else:
            print('warning: flag not set')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttest(self):
    self.test_halt.clear()
    while not self.test_halt.isSet():
        print('test thread running')
        time.sleep(1)


def starttest(self):
    global test
    if test.isAlive():
        print('warning: thread already running')
    else:
        test = threading.Thread(name='test', target=acttest)
        test.start()


def halttest(self):
    if not test.isAlive():
        print('warning: test thread not running')
    else:
        if not self.test_halt.isSet():
            self.test_halt.set()
            print('test thread halted')
        else:
            print('warning: flag not set')
