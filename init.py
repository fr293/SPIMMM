# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM] 
# description of function: this library is designed to perform all the functions associated with setting the microscope
# up

# libraries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cfg is a configuration library that shares its variables
# control is a library that allows direct control of the microscope hardware
# threading is used to achieve concurrency of multiple tasks
# time is used to control the speed of actions
# serial is used for communication with the hardware

import cfg
import serial
import time

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# description of parameters
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
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# open and close ports~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def open_ports():
    if not cfg.ard.isOpen():
        try:
            # readline blocks further execution until the port is connected and the arduino responds
            cfg.ard.open()
            cfg.ard.readline()
            sendcfg()
            print('arduino connected')
        except serial.SerialException:
            raise UserWarning('could not connect to arduino')

    if not cfg.las1.isOpen():
        try:
            cfg.las1.open()
            time.sleep(0.1)
            print('488nm laser connected')
        except serial.SerialException:
            print('could not connect to 488nm laser')

    if not cfg.las2.isOpen():
        try:
            cfg.las2.open()
            time.sleep(0.1)
            print('561nm laser connected')
        except serial.SerialException:
            print('could not connect to 561nm laser')

    laser_power()


def close_ports():
    cfg.ard.close()
    cfg.las1.close()
    cfg.las2.close()

# set calibration ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def setcal():
    cfg.slp = input("Input Calibration Slope >>>")
    print("Calibration Slope set as " + str(cfg.slp))
    cfg.off = input("Input Calibration Offset >>>")
    print("Calibration Offset set as " + str(cfg.off))

# make calibration ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# def makecal():

# send and read configuration parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def sendcfg():
    cfg.ard.write('SET ' + str(cfg.smt) + ' ' + str(cfg.frt) + ' ' + str(cfg.exp) + ' ' + str(cfg.htm) + ' '
                  + str(cfg.hpw) + ' ' + str(cfg.fnm) + ' ' + str(cfg.slp) + ' ' + str(cfg.off) + ' '
                  + str(cfg.dup) + ' ' + str(cfg.dlo) + ' ' + str(cfg.ste) + '\r')


def readcfg():
    cfg.ard.flushInput()
    cfg.ard.write('REP\r')
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())
    print(cfg.ard.readline())


# set laser power and update state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def laser_power():
    # the Coherent laser only takes arguments up to the nearest mW,
    # this will also cause an error if anything but a number comes in
    if cfg.las1.isOpen():
        power1 = round(cfg.pwr1, 3)
        cfg.las1.write('SOUR:POW:LEV:IMM:AMPL ' + str(power1) + ' \r')
        if cfg.lst1:
            cfg.las1.write('SOUR:AM:STAT ON\r')
        else:
            cfg.las1.write('SOUR:AM:STAT OFF\r')

    if cfg.las2.isOpen():
        power2 = round(cfg.pwr2, 3)
        cfg.las2.write('SOUR:POW:LEV:IMM:AMPL ' + str(power2) + ' \r')
        if cfg.lst2:
            cfg.las2.write('SOUR:AM:STAT ON\r')
        else:
            cfg.las2.write('SOUR:AM:STAT OFF\r')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
