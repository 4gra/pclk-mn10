#!/usr/bin/env python3
"""
Very, very basic control of a PCLK-MN10 attached to a compatible hi-fi unit.

This is not a script - it's my stream of consciousness / workbook.  
Tools might follow.

These tools with errant parameters could quite feasibly cause permanent
damage to a connected USB or onward hifi device: If this script bricks your
precious electronics YOU WERE WARNED.  However, it hasn't done to mine at
time of writing (and I don't have any spares).

Copyright (C) 2017, https://github.com/4gra/pclk-mn10
This program comes with ABSOLUTELY NO WARRANTY; for details see included LICENCE.
This is free software, and you are welcome to redistribute it under certain
conditions; view the included file LICENCE for details.

Requires PyUSB, etc.
"""
import sys, os, time
try:
    import usb.core
    import usb.util
except ImportError as err:
    print("Import error (%s): test mode only" % err, file=sys.stderr)

__usage__ = """\
Usage: stub.py [--test] <command>
Where <command> is one of:
  asend 'XX XX XX' ['XX XX XX' [...]]
   (sends arbitrary bytes, automatically prepending appropriate header)
  send 'XX XX XX' ['XX XX XX' [...]]
   (sends arbitrary bytes)
  read [bytes]
   (reads a maximum of [bytes] bytes, default 32)
  poll [--noascii] [bytes] 
   (reads once per second)
Or one of the named commands:
%s
"""

# endpoints, so we can preload them
EP = None
REP = None

# command list
commandlist="commands.json"
print_ascii=True

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


def dtext(word):
    """Silly ASCII printout helper"""
    return "%1s"%chr(word) if (word > 31 and word < 127) else '' if word == 0 else '?'

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

def interpret(dat):
    """
    More experiental work at understanding the returned messages.
     
    12:36:15  < 0d 00 18 ca 63 01 ff ff ff ff 0c 23 26 00
    12:36:15 TX|.. .. .. ..  c .. .. .. .. .. ..  #  & ..
    12:36:15  < 14 00 18 ca e2 01 20 20 20 20 20 20 20 20 00 31 32 00 33 35 ff
    12:36:15 TX|.. .. .. .. .. ..                         ..  1  2 ..  3  5 ..
    """
    #for msg in [o for o in dat if len(o)]:
    msg = dat
    #print("\n=[ start ]=" + "="*60)
    if len(msg) > 0 and len(msg) < 4:
        print("SHORT Message %s" % ' '.join(["{:02x}".format(s) for s in msg]))
    elif len(msg) >= 4:
        length=msg[0]
        typ=msg[4]
        print("Message {:02x}, addr {:02x}{:02x}:{:02x}, Length {:02x}".format(
            typ, msg[1], msg[2], msg[3], length)
        )
        if typ == 0xe0:
            text="".join([ dtext(x) for x in msg[5:15] ])
            #seq = "{:02x}".format(int(msg[15:]))
            seq = msg[15:16]
            print("Display update: \"{}\" seq {}".format(text, seq))
            if len(msg[16:]):
                print(" ".join("{:02x}".format(x) for x in msg[16:]))
        if len(msg[5:]):
            print(" ".join("{:02x}".format(x) for x in msg[5:]))
    print("=[  end  ]=" + "="*60 + "\n")

def xprint(dat, pre="", asc=None):
    print("%s%s" % (pre, " ".join("{:02x}".format(x) for x in dat)))
    if asc or (asc == None and print_ascii == True):
        print("TX|%s"%" ".join([ "%2s"%chr(x) if (x > 31 and x < 127) else '..' for x in dat ]))

def hexin(instr):
    """converts a string or list of strings into commands"""
    for cmd in instr.split(","):
        yield [int(x, 16) for x in cmd.split(" ") if x]

def jsend(dat, asc=None):
    """just send. and print."""
    xprint(dat, ">> ", asc)
    EP.write(dat)

def jread(ll, delay=None, asc=None):
    """just read <ll bytes>, optionally waiting <delay seconds> first."""
    if delay:
        time.sleep(delay)
    out = REP.read(ll)
    while out:
        xprint(out, " < ", asc)
        out = REP.read(ll)
    sys.stdout.flush()

def send(dat):
    """sends data and reads a max. of 40 bytes back."""
    jread(32)
    jsend(dat)

def make_out_header(dat):
    """
    adds header, saving pesky length calculations
    TODO: concept of a master device (i.e. 0x90 for MD decks; 0xC0 for the "amp" in MD595)
    """
    return [(len(dat) + 2), 0x00, 0x60] + dat

def vol_to_byte(lev):
    """
    Converts a numeric volume string to an appropriate binary value.
    Shifts left three bits (i.e. multiply by 8...)
    """
    return int(hex(round(lev) << 3),16)

def volstr_to_byte(lev):
    """
    Converts a textual volume string (MIN/0 -- 31/MAX) to appropriate binary value.
    """
    if lev == "MIN":
        lev = 0
    elif lev == "MAX":
        lev = 31
    return vol_to_byte(int(lev, 10))

def byte_to_vol(vol):
    """
    Converts a volume output byte (as string) to a readable value
    """
    return int(hex(int(vol,16) >> 3),16)
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
            os.environ['HOME'] if 'HOME' in os.environ else False,
            os.environ['USERPROFILE'] if 'USERPROFILE' in os.environ else False
        ]:
            try:
                with open(os.path.join(path,commandlist)) as f:
                    #print("Attempting %s..." % os.path.join(path,commandlist),file=sys.stderr)
                    commands.update(json.load(f))
                    if commands:
                        return commands
            except BaseException as e:
                print(e, file=stderr)
        print("Cannot load extra commands, continuing anyway.",file=sys.stderr)
    return commands


def setup_pipes(test=False, force=False):
    global EP, REP
    if test:
        td = debug_pipe(sys.stdout)
        (EP, REP) = (td, td)
    elif EP is None or REP is None or force == True:
        (EP, REP) = get_pipes()

def run(args):
    """
    Run the code!
    """
    # Unfortunately I haven't bothered to clean this up properly
    # so I am just going to insert some spurious first argument...
    argv = ['control'] + args
    try:
        if len(argv) > 1 and argv[1] == '--test':
            setup_pipes(test=True)
            argv.pop(1)
        else:
            setup_pipes(test=False)
    except IOError as err:
        print(err,file=sys.stderr)
        print("Use --test flag to continue without device.",file=sys.stderr)
        exit(1)

    # TODO: handle parameters, such as volume (basically all of them), which need interpretation
    if len(argv) > 2 and "vol" == argv[1]:
        #TODO: if argv[2] == 'up'
        #TODO: if argv[2] == 'down'
        level=volstr_to_byte(argv[2])
        jread(32)
        jsend([0x05,0x00,0x60,0xc0,0xc8]+[level])
        jread(32)
    elif len(argv) == 3 and "volsp" == argv[1]:
        # Shairport-sync volume goes from 0 to -30 (dB); -144 is 'mute'
        if argv[2] == '-144':
            level = 0
        else:
            level = (30+float(argv[2]))*0.8
            print("got %s, converted to %d" % (argv[2], level))
            level=vol_to_byte(level)
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
    elif "asend" in argv[1:] and len(argv) > 2:
        for arg in argv[2:]:
            for x in hexin(arg):
                send(make_out_header(x))
                jread(32, 0.2)
    elif "send" in argv[1:] and len(argv) > 2:
        for arg in argv[2:]:
            for x in hexin(arg):
                send(x)
                jread(32, 0.2)
    elif argv[0][-2:] == 'poll' or "poll" in argv[1:]:
        asc = ('--noascii' not in argv[1:])
        while True:
            jread(32, 0.1, asc)
    elif len(argv) > 1 and argv[1] in load_commands():
        rest = argv[1:]
        while len(rest) and rest[0] in load_commands():
            cmdname = rest.pop(0)
            mkheader = True
            cmdstr = commands[cmdname]
            # handle parameters, if given (rather spurious error will be thrown if
            # insufficient args are given). This will also screw things up if we
            # define non-sequential placeholders ... why did I do this at all?
            for i, arg in enumerate(rest):
                placeholder = "$"+str(i+1)
                if placeholder in cmdstr:
                    cmdstr = cmdstr.replace(placeholder, arg)
                else:
                    break
            if cmdstr.startswith("verbatim"):
                mkheader = False
                cmdstr = cmdstr[9:]
            cmd = hexin(cmdstr)
            for word in cmd:
                if mkheader:
                    send(make_out_header(word))
                else:
                    send(word)
                jread(32, 0.2)
                jread(32, 0.2)
    else:
        ckeys=[x for x in load_commands().keys()]
        ckeys.sort()
        print(__usage__ % "\n".join(["  %s" % x for x in ckeys]), file=sys.stderr)


if __name__ == '__main__':
    run(sys.argv[1:])
