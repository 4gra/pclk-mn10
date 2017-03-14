#!/usr/bin/env python3
# Very, very basic control of a PCLK-MN10 attached to a compatible hi-fi unit.
#
# This is not a script - it's my stream of consciousness / workbook.  
# Tools might follow.
#
# These tools with errant parameters could quite feasibly cause permanent
# damage to a connected USB or onward hifi device: If this script bricks your
# precious electronics YOU WERE WARNED.  However, it hasn't done to mine at
# time of writing (and I don't have any spares).
#
# Copyright (C) 2017, https://github.com/4gra/pclk-mn10
# This program comes with ABSOLUTELY NO WARRANTY; for details see included LICENCE.
# This is free software, and you are welcome to redistribute it under certain
# conditions; view the included file LICENCE for details.
#
# Requires PyUSB, etc.
import usb.core
import usb.util
import time

# Do the device setup.
dev = usb.core.find(idVendor=0x054C,idProduct=0x0034)
dev.set_configuration()
cfg = dev.get_active_configuration()
# print(cfg)
intf = cfg[(0,0)]
def finder(mask):
    return lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == mask

ep  = usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_OUT))  # 0x01
rep = usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_IN))  # 0x82
# print ("Found %s." % [ep, rep])


"""
We _were_ going to attempt to figure out control commands but that was unneeded.

The windows driver (and this library) send something (very close to):
# SETUP PACKET:
#    80 06 00 01 00 00 12 00

>>> dev.ctrl_transfer(0x80, 0x06, 0x0100, 0, 0x12)
array('B', [18, 1, 16, 1, 255, 0, 0, 64, 76, 5, 52, 0, 0, 1, 1, 2, 0, 1])

# SETUP PACKET:
#   80 06 00 02 00 00 09 02

>>> dev.ctrl_transfer(0x80, 0x06, 0x0002, 0, 0x0902)
array('B', [9, 2, 32, 0, 1, 1, 2, 128, 50, 9, 4, 0, 0, 2, 0, 0, 0, 0, 7, 5, 1, 2, 64, 0, 0, 7, 5, 130, 2, 64, 0, 0])

# Finally a write/read seemed to do something -- just the once...
>>> ep.write([0x00,0x60,0x00])
3
>>> rep.read(40)
array('B', [0, 96, 17, 0, 100])
>>> ep.write([0x00,0x60,0x00])
3
>>> rep.read(40)
array('B')
# it transpires that the device had become confused somehow; a replug
# determined that this was indeed the poweron command.
"""

def xprint(dat, pre=""):
    print("%s%s" % (pre, " ".join("{:02x}".format(x) for x in dat)))

def jsend(dat):
    """just send. and print."""
    xprint(dat, ">> ")
    ep.write(dat)

def jread(ll, delay=None):
    if delay:
        time.sleep(delay)
    out = rep.read(ll)
    while out:
        xprint(out, " < ")
        out = rep.read(ll)
    stdout.flush()

def send(dat):
    """sends data and reads a max. of 40 bytes back."""
    jread(32)
    jsend(dat)

if __name__ == '__main__':
    from sys import argv, stdout

    if argv[0][-3:] == 'off' or "off" in argv[1:]:
        print("Off...")
        jread(32)
        jsend([0x04,0x00,0x60,0xc0,0x2f])  # ASCII 4F := 'O'
        jsend([0x04,0x00,0x60,0xb0,0x26])  # ASCII 46 := 'F' 
        #send([0x04,0x00,0x60,0x90,0x26])  # ASCII 46 := 'F' 
        jread(32, 0.2)
    elif argv[0][-2:] == 'on' or "on" in argv[1:]:
        print("On...")
        send([0x00,0x60,0x00])
        jread(32, 0.5)
    elif argv[0][-2:] == 'poll' or "poll" in argv[1:]:
        while True:
            jread(32)

    else:
        print("Usage: stub.py [on|off|thing}")

