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
import sys

# command list
commandlist="commands.json"

def get_pipes():
    """Do the device setup."""
    dev = usb.core.find(idVendor=0x054C,idProduct=0x0034)
    if not dev:
        print("Cannot find PCLK-MN10 device; exiting.",file=sys.stderr)
        sys.exit(1)

    dev.set_configuration()
    cfg = dev.get_active_configuration()
    # print(cfg)
    intf = cfg[(0,0)]
    def finder(mask):
        return lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == mask

    return (usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_OUT)),  # 0x01
            usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_IN)))  # 0x82
    # print ("Found %s." % [ep, rep])

(ep, rep) = get_pipes()

def xprint(dat, pre=""):
    print("%s%s" % (pre, " ".join("{:02x}".format(x) for x in dat)))

def hexin(instr):
    """converts a string or list of strings into commands"""
    for cmd in instr.split(","):
        yield [int(x, 16) for x in cmd.split(" ") if x]

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

commands = {
}
def read_commands():
    if not commands:
        try:
            import json
            commands.update(
                json.load(open(commandlist))
            )
        except:
            print("Cannot read extra commands, continuing anyway.",file=sys.stderr)
    return commands

if __name__ == '__main__':
    from sys import argv, stdout

    if argv[0][-3:] == 'off' or "off" in argv[1:]:
        print("Off...")
        jread(32)
        jsend([0x04,0x00,0x60,0xc0,0x2f])  # ASCII 4F := 'O'
        #jsend([0x04,0x00,0x60,0xb0,0x26])  # ASCII 46 := 'F' 
        #send([0x04,0x00,0x60,0x90,0x26])  # ASCII 46 := 'F' 
        jread(32, 0.2)
    elif "read" in argv[1:]:
        jread(32)
    elif "send" in argv[1:] and len(argv) > 2:
        for arg in argv[2:]:
            for x in hexin(arg):
                send(x)
                jread(32, 0.2)
    elif argv[0][-2:] == 'on' or "on" in argv[1:]:
        print("On...")
        send([0x00,0x60,0x00])
        jread(32, 0.5)
    elif argv[0][-2:] == 'poll' or "poll" in argv[1:]:
        while True:
            jread(32)
    # TODO: precompile this list once we are no longer
    # adding to it continually!
    elif len(argv) > 1 and argv[1] in read_commands():
        for x in hexin(commands[argv[1]]):
            send(x)
            jread(32, 0.2)
            jread(32, 0.2)
    else:
        print("""\
Usage: stub.py <command>
Where <command> is one of:
  send 'XX XX XX' ['XX XX XX' [...]]
  read [bytes]
  poll
Or one of the named commands:
%s
""" % "\n".join(["  %s" % x for x in read_commands().keys()]))

