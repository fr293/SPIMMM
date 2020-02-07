# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM] 
# description of function: this library communicates with the hardware of the microscope at a basic level.

# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cfg is a configuration library that shares its variables

import cfg
import init
import re
import time
import math

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# description of parameters
#
# functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

errorsum = 0.0

# functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# move mirror ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def mirror(count):
    # only integers are permitted,
    # this will also cause an error if anything but a number comes in
    count = int(count)
    cfg.ard.write('DAC ' + str(count) + '\r')


# move stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def stage(position):
    # the PI stage only takes arguments up to the nearest nanometer,
    # this will also cause an error if anything but a number comes in
    position = round(position, 6)
    cfg.ard.write('STA ' + str(position) + '\r')


# halt stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def hlt():
    # trigger the halt command on the PI stage
    cfg.ard.write('STP ' + '\r')


# halt stage ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def rbt():
    # trigger the reboot command on the PI stage
    cfg.ard.write('RBT ' + '\r')


# take frame ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def frame(length):
    # only integers are permitted, this will also cause an error if anything but a number comes in
    length = int(length)
    cfg.ard.write('FRM ' + str(length) + '\r')



# move stage and mirror together ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def focus(location):
    stage(location)
    mirror(stm(location))


# calculate mirror count for focus ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def stm(stage_dist):
    mirror_count = (stage_dist * cfg.slp) + cfg.off

    return mirror_count


# extrapolate conservative estimate of large stage movement time ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def pau(stage_move):
    pause = cfg.smt*(stage_move/cfg.ste)
    pause = round(pause, 6)

    return pause


# take a volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def tkv():
    cfg.ard.flushInput()
    tic = time.time()
    cfg.ard.write('RUN\r')
    resp = cfg.ard.readline()
    toc = time.time()
    print(resp)
#    print(toc-tic)


# reset error state ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def err():
    cfg.ard.write('ERR\r')


# push heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def sdh():
    cfg.ard.write('STH\r')


# read heater parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def rdh():
    cfg.ard.flushInput()
    cfg.ard.write('RDH\r')
    resp = cfg.ard.readline()
    if 'END' in resp:
        return resp
    else:
        print('temperature poll error')
        time.sleep(0.1)
        rdh()


# read heater parameters and control temperature~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def clt():
    global errorsum
    global ontarget

#   count is the number of polling periods that the bath must within +- 1 degree of the set point to be on target
#   maxsig is the maximum signal that can be sent to the temperature driver board
#   coolingfactor is the proportion of maximum power that can be applied in cooling mode

    count = 100
    maxsig = 799
    coolingfactor = 0.75

    maxerrorsum = maxsig/cfg.tki

#   extract measured temperature from readout
#   we may want to refactor the extraction as a function that takes a keyword and a string, and returns the value of the
#   argument after it, though given that we're dealing with mixed data types, this might be more difficult than it is
#   useful
#    paramstring = "$HC,MODE,1,PWM,400,TEMP,26.5,END"

    paramstring = cfg.tcr
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
    temperror = cfg.tem - tempm

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
        errorsum = errorsum + (temperror*cfg.ttc)
    else:
        errorsum = 0

    # if abs(errorsum) > maxerrorsum:
    #     if errorsum > 0:
    #         errorsum = maxerrorsum
    #     else:
    #         errorsum = -maxerrorsum * coolingfactor

    if errorsum > maxerrorsum:
        errorsum = maxerrorsum
    elif errorsum < 0:
        errorsum = 0

    if cfg.tst:
        signal = 500
    elif temperror < 0 :
        signal = (temperror * cfg.tkpc) + (errorsum * cfg.tki)
    else:
        signal = (temperror * cfg.tkp) + (errorsum * cfg.tki)

    if signal > maxsig:
        signal = maxsig
    elif signal < -(maxsig*coolingfactor):
        signal = -(maxsig*coolingfactor)

    cfg.hpw = abs(signal)

    if signal >= 0:
        cfg.htm = 2
        cfg.fnm = 0


    else:
        cfg.htm = 1
        cfg.fnm = 1

# if abs(signal) > maxsig:
#     signal = math.copysign(maxsig, signal)
# cfg.hpw = abs(signal)

# set the peltier mode appropriately
# throttle down the maximum on the cooling side to prevent self-heating dominating
#     if signal >= 0:
#         cfg.htm = 2
#     else:
#         cfg.htm = 1
#         cfg.hpw = coolingfactor * cfg.hpw



    if cfg.dbg:
        print('demand temperature: ' + str(cfg.tem) + ', ' + 'measured temperature: ' + str(tempm))
        print('proportional signal: ' + str(temperror * cfg.tkp) + ', ' + 'integral signal: '
              + str((errorsum * cfg.tki)))
        print('signal: ' + str(signal) + ', ' + 'heater power: ' + str(cfg.hpw) + ', ' + 'heater mode: ' + str(cfg.htm))
        if ontarget:
            print('on target')

            # set the peltier duty cycle and throttle down to the maximum set above

# send the parameters and push to the heater
    init.sendcfg()
    sdh()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
