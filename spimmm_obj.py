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
# ers - total error for the heater controller
#
# ont - boolean value indicating if the temperature controller is on target
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
# cur1 - the first coil's current value in mA
#
# cur2 - the first coil's current value in mA
#
# cur3 - the first coil's current value in mA
#
# cur4 - the first coil's current value in mA
#
# led - the white led's intensity value 0-1023
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
# engage - engages the stage by communicating with the arduino
#
# disengage - disengages the stage by communicating with the arduino
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
# setmag - set the current value of all magnet channels, note that this also requires a hard or soft trigger
#
# setled - set the led intensity value
#
# readmag - read the magnet controller status
#
# trigmag - trigger the magnet controller on or off in software
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
        self.get_pos()
        self.laser_power()

    # variables ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    dbg = True

    smt = 20

    frt = 25

    exp = 10

    tcr = ''

    htm = 0

    hpw = 0

    fnm = 0

    tem = 17

    ttc = 1

    tkp = 120

    tkpc = 600

    tki = 1.5

    ers = 0

    ont = False

    tst = False

    lgp = 1

    plp = 0.1

    slp = -4486.982

    posadj = 6.1

    off = int(posadj*slp)

    dup = 6.3

    dlo = 6.0

    ste = 0.02

    pos = 0.0

    imt = 30

    vrt = 0.5

    pwr1 = 0.010

    pwr2 = 0.010

    lst1 = False

    lst2 = False

    cur1 = 0

    cur2 = 0

    cur3 = 0

    cur4 = 0

    led = 0

    camera2=4

    num_frame=5

    frame_period=500 #ms



    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # serial objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

    # threading objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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



        self.seriallock.acquire()
        self.ard.write(
            'SET {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12} {13} {14} {15} {16} {17} {18}\r'.format(str(self.smt),
                                                                                                 str(self.frt),
                                                                                                 str(self.exp),
                                                                                                 str(self.htm),
                                                                                                 str(self.hpw),
                                                                                                 str(self.fnm),
                                                                                                 str(self.cur1),
                                                                                                 str(self.cur2),
                                                                                                 str(self.cur3),
                                                                                                 str(self.cur4),
                                                                                                 str(self.led),
                                                                                                 str(self.slp),
                                                                                                 str(self.off),
                                                                                                 str(self.dup),
                                                                                                 str(self.dlo),
                                                                                                 str(self.ste),
                                                                                                    str(self.camera2),
                                                                                                    str(self.num_frame),
                                                                                                    str(self.frame_period)))
        self.seriallock.release()

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

    # set laser power and update state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def laser_power(self):
        # the Coherent laser only takes arguments up to the nearest mW,
        # this will also cause an error if anything but a number comes in
        if self.las1.isOpen():
            try:
                if self.pwr1 > 0.0:
                    power1 = round(self.pwr1, 3)
                    print('488nm laser set to ' + str(power1 * 1000) + 'mW')
                    self.las1.write('SOUR:AM:INT\r')
                    self.las1.write('SOUR:POW:LEV:IMM:AMPL ' + str(power1) + ' \r')
                else:
                    print('488nm laser power must be positive')
            except TypeError:
                print('488nm laser power set incorrectly')
            if self.lst1:
                self.las1.write('SOUR:AM:STAT ON\r')
            else:
                self.las1.write('SOUR:AM:STAT OFF\r')
        else:
            print('error: 488nm laser not connected')

        if self.las2.isOpen():
            try:
                if self.pwr2 > 0.0:

                    power2 = round(self.pwr2, 3)
                    print('561nm laser set to ' + str(power2 * 1000) + 'mW')
                    self.las2.write('SOUR:AM:INT\r')
                    self.las2.write('SOUR:POW:LEV:IMM:AMPL ' + str(power2) + ' \r')
                else:
                    print('561nm laser power must be positive')
            except TypeError:
                print('561nm laser power set incorrectly')
            if self.lst2:
                self.las2.write('SOUR:AM:STAT ON\r')
            else:
                self.las2.write('SOUR:AM:STAT OFF\r')
        else:
            print('error: 561nm laser not connected')

    # move mirror ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def mirror(self, count):
        # only integers are permitted,
        # this will also cause an error if anything but a number comes in
        try:
            count = int(count)
            print('hey')
            self.seriallock.acquire()
            self.ard.write('DAC ' + str(count) + '\r')
            self.seriallock.release()
            # resp = self.ard.readline()  # ]
            # print(resp)
            # while resp!="o\n":
            #     resp = self.ard.readline()#]
            #     print(resp)
            #print(resp)
            # print('hey')

        except ValueError:
            print('error: mirror value not an int')

    # move stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
            # if the distance is over 10 microns, move slowly, otherwise move fast
            self.seriallock.acquire()
            if distance >= 0.010:
                self.ard.write('STS ' + str(self.pos) + '\r')
            else:
                self.ard.write('STA ' + str(self.pos) + '\r')
            self.seriallock.release()
        except TypeError:
            print('error: position value not a float')

    # get stage position ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_pos(self):
        # return the position of the PI stage in mm
        self.seriallock.acquire()
        self.ard.write('QRP\r')
        self.seriallock.release()
        resp = self.ard.readline()
        self.pos = float(resp)

    # halt stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def hlt(self):
        # trigger the halt command on the PI stage
        self.seriallock.acquire()
        self.ard.write('STP ' + '\r')
        self.seriallock.release()

    # reboot stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def rbt(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('RBT ' + '\r')
        self.seriallock.release()

    # engage stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def engage(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('ENG ' + '\r')
        self.seriallock.release()


    # disengage stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def disengage(self):
        # trigger the reboot command on the PI stage
        self.seriallock.acquire()
        self.ard.write('DNG ' + '\r')
        self.seriallock.release()

    # take frame ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def frame(self, cam, length):
        # only integers are permitted, this will also cause an error if anything but a number comes in
        try:
            cam = int(cam)
            length = int(length)
            self.seriallock.acquire()
            self.ard.write('FRM ' + str(cam) + ' ' + str(length) + '\r')
            self.seriallock.release()
        except ValueError:
            print('frame length set incorrectly')

    # move stage and mirror together ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def focus(self, location):
        #the command order here is important! See Stage
        self.mirror(self.stm(location))
        self.stage(location)


    # calculate mirror count for focus ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def stm(self, stage_dist):
        self.off = int(self.posadj * self.slp)
        mirror_count = int(((stage_dist - self.posadj)* self.slp) +4095)
        print(mirror_count)
        if mirror_count > 4095:
            mirror_count = 4095
            print('warning: mirror out of range')
        if mirror_count < 0:
            mirror_count = 0
            print('warning: mirror out of range')

        return mirror_count

    # extrapolate conservative estimate of large stage movement time ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def pau(self, stage_move):
        pause = self.smt * (stage_move / self.ste)
        pause = round(pause, 6)
        return pause

    # take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def tkv(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('RUN\r')
        self.seriallock.release()

    #take multiple volumes in a row
    def tkvm(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('RUNM\r')
        self.seriallock.release()


    # reset error state from the stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def err(self):
        self.ard.flushInput()
        self.seriallock.acquire()
        self.ard.write('ERR\r')
        resp = self.ard.readline()
        resp = resp + self.ard.readline()
        self.seriallock.release()
        print(resp)
        return(resp)

    # push heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def sdh(self):
        self.seriallock.acquire()
        self.ard.write('STH\r')
        self.seriallock.release()

    # read heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
            self.rdh()

    # read heater parameters and control temperature~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
            tempm = float(tempstring)
        else:
            tempm = int(tempstring)

        # calculate the error and set the parameters
        temperror = self.tem - tempm

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
            print('demand temperature: ' + str(self.tem) + ', ' + 'measured temperature: ' + str(tempm))
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






# set the current channels ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def setmag(self):
    self.seriallock.acquire()
    self.ard.write('STM\r')
    self.seriallock.release()


# set the white led intensity ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def setled(self):
    self.seriallock.acquire()
    self.ard.write('LON\r')
    self.seriallock.release()


# read the magnet system state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def readmag(self):
    self.seriallock.release()
    self.ard.write('RDM\r')
    self.seriallock.release()
    resp = self.ard.readline()
    if 'END' in resp:
        return resp
    else:
        print('magnet poll error')


# trigger the magnet controller on or off in software ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def trigmag(self, trigger=0):
    self.seriallock.acquire()
    if trigger:
        self.ard.write('TRS\r')
    else:
        self.ard.write('KLS\r')
    self.seriallock.release()


# run camera ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# note that the sleep parameter includes the exposure time

def actcam(self, cam):
    print('camera started')

    self.camera_halt.clear()
    while not self.camera_halt.isSet():
        # self.seriallock.acquire()
        self.frame(cam, self.exp)
        # self.seriallock.release()
        time.sleep(self.frt - (0.001 * self.exp))


def startcam():
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





# run temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttempcont(self):
    if not self.temppoll.isAlive():
        starttemppoll(self)

    while not self.data_in.isSet():
        print('waiting for data')
        time.sleep(0.1)

    print('temperature control running')
    self.tempcont_halt.clear()
    while not self.tempcont_halt.isSet():
        # self.seriallock.acquire()
        self.clt()
        # self.seriallock.release()
        time.sleep(self.ttc)


def starttempcont(self):
    if self.tempcont.isAlive():
        print('warning: thread already running')
    else:
        self.ers = 0
        tempcont = threading.Thread(name='tempcont', target=acttempcont)
        tempcont.start()


def halttempcont(self):
    if not self.tempcont.isAlive():
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
        # self.seriallock.acquire()
        self.sendcfg()
        self.sdh()
        # self.seriallock.release()


# run temperature logging ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttemplog(self):
    if not self.temppoll.isAlive():
        starttemppoll(self)

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


def starttemplog(self):
    if self.templog.isAlive():
        print('warning: thread already running')
    else:
        templog = threading.Thread(name='templog', target=acttemplog)
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
        # self.seriallock.acquire()
        self.tcr = self.rdh()
        # self.seriallock.release()
        self.data_in.set()
        time.sleep(self.plp)
    self.data_in.clear()


def starttemppoll(self):
    if self.temppoll.isAlive():
        print('warning: thread already running')
    else:
        self.temppoll = threading.Thread(name='temppoll', target=acttemppoll)

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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttest(self):
    self.test_halt.clear()
    while not self.test_halt.isSet():
        print('test thread running')
        time.sleep(1)


def starttest(self):
    if self.test.isAlive():
        print('warning: thread already running')
    else:
        test = threading.Thread(name='test', target=acttest)
        test.start()


def halttest(self):
    if not self.test.isAlive():
        print('warning: test thread not running')
    else:
        if not self.test_halt.isSet():
            self.test_halt.set()
            print('test thread halted')
        else:
            print('warning: flag not set')

# take volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def actvol(self):
    self.sendcfg()
    print('microscope running')
    self.volume_halt.clear()
    while not self.volume_halt.isSet():
        # self.seriallock.acquire()
        self.tkv()
        # self.seriallock.release()

def startvol(self):
    global volume
    if volume.isAlive():
        print('warning: thread already running')
    else:
        volume = threading.Thread(name='volume', target=self.actvol)
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