# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM] 
# description of function: this library holds the fixed parameters that are used by all the operational functions


# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# serial is used for communication with the hardware

import serial

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
# serial objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# ard - arduino COM port; the COM port that the OS assigns to the arduino,
# which runs the mirror and camera triggering software
#
# las1 - 488nm laser COM port; the COM port that the OS assigns to the coherent laser
#
# las2 - 561nm laser COM port; the COM port that the OS assigns to the coherent laser
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


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

off = 14324

dup = 6.4

dlo = 5.9

ste = 0.005

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
