# fergus riche fr293 wrote this to control the Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM]
# description of function: this library is used to conduct experiments .

# libraries to import ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cfg is a configuration library that shares its variables
# main is a high level library that brings together the functions of the lower libraries
# time is used to measure time

import cfg
import init
import ctrl
import main
import time


def tempstep():
    init.open_ports()
    main.starttemplog()
    time.sleep(300)
    # set heater parameters to make a step
    cfg.tst = True
    main.starttempcont()
    time.sleep(1800)
    main.halttempcont()
    time.sleep(300)
    main.halttemplog()


def tempcontrolrecord():
    init.open_ports()
    main.starttemplog()
    time.sleep(300)
    cfg.dbg = True
    # set heater parameters to make a step
    cfg.tem = 40
    main.starttempcont()
    time.sleep(1200)
    cfg.tem = 20
    time.sleep(2700)
    main.halttempcont()
    time.sleep(5)
    cfg.dbg = False
    main.halttemplog()
    main.halttemppoll()


def setup():
    init.open_ports()
    raw_input('Press Enter to Raise Objective')
    ctrl.stage(-6.4)
    raw_input('Press Enter to Lower Objective')
    ctrl.stage(cfg.dup)
