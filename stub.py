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
import sys, os, time

# command list
commandlist="commands.json"

class debug_pipe:
    """
    Returns two virtual USB pipes which simply relay communication to stdout.
    """
    def __init__(self, afile):
        self.afile = afile

    def write(self, data):
        self.afile.write(">>(%s)\n" % " ".join(["%02x" % x for x in data]))

    def read(self, ll):
        self.afile.write(" < .. (read ≤%s bytes)\n" % ll)


def get_pipes():
    """
    Performs device setup.
    Returns two USB endoints for (write, read).
    """
    dev = usb.core.find(idVendor=0x054C,idProduct=0x0034)
    if not dev:
        raise IOError("Cannot find PCLK-MN10 device")

    dev.set_configuration()
    cfg = dev.get_active_configuration()
    # print(cfg)
    intf = cfg[(0,0)]
    def finder(mask):
        return lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == mask

    return (usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_OUT)),  # 0x01
            usb.util.find_descriptor(intf, custom_match=finder(usb.util.ENDPOINT_IN)))  # 0x82
    # print ("Found %s." % [ep, rep])

def xprint(dat, pre="", asc=True):
    print("%s%s" % (pre, " ".join("{:02x}".format(x) for x in dat)))
    if asc:
        print("TX|%s"%" ".join([ "%2s"%chr(x) if (x > 31 and x < 127) else '..' for x in dat ]))

def hexin(instr):
    """converts a string or list of strings into commands"""
    for cmd in instr.split(","):
        yield [int(x, 16) for x in cmd.split(" ") if x]

def jsend(dat):
    """just send. and print."""
    xprint(dat, ">> ")
    ep.write(dat)

def jread(ll, delay=None):
    """just read <ll bytes>, optionally waiting <delay seconds> first."""
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

def vol_to_byte(lev):
    """
    Converts a textual volume string (MIN/0 -- 31/MAX) to appropriate binary value.
    (Basically just multiplies by 8...)
    """
    if lev == "MIN":
        lev = 0
    elif lev == "MAX":
        lev = 31
    return int(lev)*8

def byte_to_vol(vol):
    """
    Converts a volume output byte to a readable value
    """
    return int(vol,16)/8

commands = {
}

# TODO: precompile this list once we are no longer
# adding to it continually!
def load_commands():
    if not commands:
        import json
        for path in [
            os.path.dirname(os.path.realpath(__file__)),
            os.getcwd(),
            os.environ['HOME']
        ]:
            try:
                with open(os.path.join(path,commandlist)) as f:
                    #print("Attempting %s..." % os.path.join(path,commandlist),file=sys.stderr)
                    commands.update(json.load(f))
                    if commands:
                        return commands
            except:
                pass
        print("Cannot load extra commands, continuing anyway.",file=sys.stderr)
    return commands


if __name__ == '__main__':
    from sys import argv, stdout, stderr
    if len(argv) > 1 and argv[1] == '--test':
        argv.pop(1)
        td = debug_pipe(stdout)
        (ep, rep) = (td, td)
    else:
        try:
            (ep, rep) = get_pipes()
        except IOError as err:
            print(err,file=stderr)
            print("Use --test flag to continue without device.",file=stderr)
            exit(1)
    if "off" in argv[1:2]:
        jread(32)
        jsend([0x04,0x00,0x60,0xc0,0x2f])
        # TODO: take state
        jread(32, 0.2)
    elif "on" in argv[1:2]:
        send([0x00,0x60,0x00])
        # TODO: take state
        jread(32, 0.2)
    elif len(argv) > 2 and "vol" == argv[1]:
        #TODO: if argv[2] == 'up'
        #TODO: if argv[2] == 'down'
        level=vol_to_byte(argv[2])
        jread(32)
        jsend([0x05,0x00,0x60,0xc0,0xc8]+[level])
        jread(32)
    elif "read" in argv[1:]:
        try:
            ll=int(argv[2])
        except:
            ll=32
        finally:
            jread(ll)
    elif "send" in argv[1:] and len(argv) > 2:
        for arg in argv[2:]:
            for x in hexin(arg):
                send(x)
                jread(32, 0.2)
    elif argv[0][-2:] == 'poll' or "poll" in argv[1:]:
        while True:
            jread(32)
    elif len(argv) > 1 and argv[1] in load_commands():
        # TODO: arguments ending in "_" take parameters.
        if argv[1][-1] == "_":
            print("Parameterised options not yet supported, sorry.")
            sys.exit(1)
        for x in hexin(commands[argv[1]]):
            send(x)
            jread(32, 0.2)
            jread(32, 0.2)
    else:
        ckeys=[x for x in load_commands().keys()]
        ckeys.sort()
        print("""\
Usage: stub.py [--test] <command>
Where <command> is one of:
  send 'XX XX XX' ['XX XX XX' [...]]
   (sends arbitrary bytes)
  read [bytes]
   (reads a maximum of [bytes] bytes, default 32)
  poll
Or one of the named commands:
%s
""" % "\n".join(["  %s" % x for x in ckeys]),file=stderr)

