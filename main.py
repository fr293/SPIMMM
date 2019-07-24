# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM] 
# description of function: this library communicates with the hardware of the microscope at a high level.

# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cfg is a configuration library that shares its variables
# control is a library that allows direct control of the microscope hardware
# threading is used to achieve concurrency of multiple tasks
# time is used to measure time

import cfg
import init
import ctrl
# import serial
import threading
import time

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# description of parameters
#
# objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# run camera ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# note that the sleep parameter includes the exposure time


def actcam():
    print('camera started')

    camera_halt.clear()
    while not camera_halt.isSet():
        seriallock.acquire()
        ctrl.frame(cfg.exp)
        seriallock.release()
        time.sleep(cfg.frt - (0.001 * cfg.exp))


def startcam():
    global camera
    if camera.isAlive():
        print('warning: thread already running')
    else:
        camera = threading.Thread(name='camera', target=actcam)
        camera.start()


def haltcam():
    if not camera.isAlive():
        print('warning: camera not running')
    else:
        if not camera_halt.isSet():
            camera_halt.set()
            print('camera acquisition halted')
        else:
            print('warning: flag not set')


# take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def actvol():
    init.sendcfg()
    print('microscope running')
    volume_halt.clear()
    while not volume_halt.isSet():
        seriallock.acquire()
        ctrl.tkv()
        seriallock.release()


def startvol():
    global volume
    if volume.isAlive():
        print('warning: thread already running')
    else:
        volume = threading.Thread(name='volume', target=actvol)
        volume.start()


def haltvol():
    if not volume.is_alive():
        print('warning: volume acquisition not running')
    else:
        if not volume_halt.isSet():
            volume_halt.set()
            print('volume acquisition halted')
        else:
            print('warning: flag not set')


# run temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttempcont():
    if not temppoll.isAlive():
        starttemppoll()

    while not data_in.isSet():
        print('waiting for data')
        time.sleep(0.1)

    print('temperature control running')
    tempcont_halt.clear()
    while not tempcont_halt.isSet():
        seriallock.acquire()
        ctrl.clt()
        seriallock.release()
        time.sleep(cfg.ttc)


def starttempcont():
    global tempcont
    if tempcont.isAlive():
        print('warning: thread already running')
    else:
        ctrl.errorsum = 0
        tempcont = threading.Thread(name='tempcont', target=acttempcont)
        tempcont.start()


def halttempcont():
    if not tempcont.isAlive():
        print('warning: temperature control not running')
    else:
        if not tempcont_halt.isSet():
            tempcont_halt.set()
            temppoll_halt.set()
            print('temperature control halted')
        else:
            print('warning: flag not set')

# shut the heater controller down
        cfg.htm = 0
        cfg.fnm = 0
        seriallock.acquire()
        init.sendcfg()
        ctrl.sdh()
        seriallock.release()


# run temperature logging ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttemplog():
    if not temppoll.isAlive():
        starttemppoll()

    while not data_in.isSet():
        print('waiting for data')
        time.sleep(0.1)

    print('temperature logging running')
    timestr = time.strftime('%Y%m%d-%H%M%S')
    contstring = 'Kp' + '_' + str(cfg.tkp) + '_' + 'Ki' + '_' + str(cfg.tki)
    templogname = 'templog_' + timestr + '_' + contstring + '.csv'
    templogname = 'templog/' + templogname
    templogfile = open(templogname, 'a')
    templogfile.write('Device,,Mode,,PWM,,Temp,,\n')

    templog_halt.clear()
    while not templog_halt.isSet():
        templogfile.write(cfg.tcr.rstrip() + ',' + 'SET TEMP' + ',' + str(cfg.tem) + ',' + 'SYS TIME' + ','
                          + str(time.time()) + '\n')
        time.sleep(cfg.lgp)
    templogfile.close()


def starttemplog():
    global templog
    if templog.isAlive():
        print('warning: thread already running')
    else:
        templog = threading.Thread(name='templog', target=acttemplog)
        templog.start()


def halttemplog():
    if not templog.isAlive():
        print('warning: temperature logging not running')
    else:
        if not templog_halt.isSet():
            templog_halt.set()
            temppoll_halt.set()
            print('temperature logging halted')
        else:
            print('warning: flag not set')


# poll temperature control board ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def acttemppoll():
    if not cfg.ard.isOpen():
        print('warning: port is not open')
        print('attempting to open')
        try:
            init.open_ports()
            print('ports opened successfully')
        except UserWarning:
            print('ports unreachable, releasing thread locks in 2 seconds')
            time.sleep(2)
            seriallock.release()
            return

    temppoll_halt.clear()
    while not temppoll_halt.isSet():
        seriallock.acquire()
        cfg.tcr = ctrl.rdh()
        seriallock.release()
        data_in.set()
        time.sleep(cfg.plp)
    data_in.clear()


def starttemppoll():
    global temppoll
    if temppoll.isAlive():
        print('warning: thread already running')
    else:
        temppoll = threading.Thread(name='temppoll', target=acttemppoll)

        temppoll.start()


def halttemppoll():
    if not temppoll.isAlive():
        print('warning: temperature polling not running')
    else:
        if not temppoll_halt.isSet():
            temppoll_halt.set()
            print('temperature polling halted')
        else:
            print('warning: flag not set')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def acttest():
    test_halt.clear()
    while not test_halt.isSet():
        print('test thread running')
        time.sleep(1)


def starttest():
    global test
    if test.isAlive():
        print('warning: thread already running')
    else:
        test = threading.Thread(name='test', target=acttest)
        test.start()


def halttest():
    if not test.isAlive():
        print('warning: test thread not running')
    else:
        if not test_halt.isSet():
            test_halt.set()
            print('test thread halted')
        else:
            print('warning: flag not set')
