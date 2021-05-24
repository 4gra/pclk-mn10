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
import sys, os, time, traceback
try:
    import usb.core
    import usb.util
except ImportError as err:
    print("Import error (%s): test mode only" % err, file=sys.stderr)
try:
    from interpret import *
except ImportError as err:
    print("Can't import interpretation module, that's OK", file=sys.stderr)
    interpret = None

__usage__ = """\
Usage: stub.py [--test] [--noascii] <command>

 Where <command> is one of:
  asend 'XX XX XX' ['XX XX XX' [...]]
   (sends arbitrary bytes, automatically building appropriate header)

  send 'XX XX XX' ['XX XX XX' [...]]
   (sends arbitrary bytes, verbatim)

  read [bytes]
   (reads a maximum of [bytes] bytes, default 32)

  poll [bytes] 
   (reads output once per second in [bytes] chunks)

  expect 'XX XX XX' ['XX XX XX' [...]] <spec> 
   Sends commands, restricting return output to those matching <spec> 
   and returning (with status 0) AS SOON AS spec is matched; 1 otherwise.

 And where options described above are:
  --noascii   prevents the default 'TX' printout lines belwo
       every line of raw hex output.
       
 And where <spec> looks like 'XX ?X X? ??', performing a string-initial search
 where ? represents a 1-byte wildcard.

 In all of the above,
  'X' is any hex digit; '?' is a literal question mark.

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


def xprint(dat, pre="", asc=None):
    print("%s%s" % (pre, " ".join("{:02x}".format(x) for x in dat)))
    if asc or (asc == None and print_ascii == True):
        print("TX|%s"%" ".join([ "%2s"%chr(x) if (x > 31 and x < 127) else '..' for x in dat ]))


def dtext(word):
    """Silly ASCII printout helper"""
    return "%1s"%chr(word) if (word >= 0x20 and word < 127) else '' if word == 0 else '?'

def textin(instr):
    """converts a string into lists of ascii numbers"""
    return [ord(cc) if (ord(cc) >= 20 and ord(cc) < 127) else '?' for cc in instr]

def split_bytes(word):
    """
    Split a word into its two bytes.
    >>> split_bytes(0xf2)
    (15, 2)
    """
    return divmod(word, 0x10)

def match_bytes(dat, matchspec, rtnword=None):
    """
    Performs an initial-substring match on a byte string.
    Returns True in case of match.
    Match spec is usual two-byte groups, '?' for a wildcard byte, '??' for both bytes
        otherwise digits specified as usual.  Empty string is not supported.
    >>> match_bytes([0x00,0x01,0x12,0xc3,0x70,0x01,0x02,0x03], '?? ?? 1? c? 70')
    True
    >>> match_bytes([0x00,0x01,0x12,0xc3,0x70,0x01,0x02,0x03], '?? ?? 1? d? 70')
    False
    >>> match_bytes([0x00,0x01,0x12,0xc3,0x70,0x01,0x02,0x03], '?? ?? 1? ?3 70')
    True
    >>> match_bytes([0x00,0x01,0x12], '0? 0? 1?')
    True
    >>> match_bytes([0x00,0x01,0x12], '??')
    True
    >>> match_bytes([0x00,0x01,0x12], '?? ?? 1? d? 70')
    False
    >>> match_bytes([0x00,0x01,0x12,0xc3,0x70,0xfe,0x02,0x03], '?? ?? 1? ?3 70', 5)
    254
    """
    matches = matchspec.split(' ')
    lastmatch = len(matches)
    if len(dat) < lastmatch:
        return False

    for i, bb in enumerate(dat):
        if i >= lastmatch:
            break
        try:
            if int(matches[i],16) == bb:
                continue
        except ValueError:
            if matches[i] == '??':
                continue
            else:
                (hi, lo) = split_bytes(bb)
                (mhi, mlo) = matches[i]
                if mhi == '?' and int(mlo,16) == lo:
                    continue
                elif mlo == '?' and int(mhi,16) == hi:
                    continue
        # fallthrough
        return False
    # we made it
    if rtnword != None:
        return dat[rtnword]
    return True

def make_chunk(msg, chunk_msg=None, string=[], limit=20, chunk_index=None):
    """
    Returns a chunked set of messages for a given string parameter
    Pads with 00,00 when complete.

    The continuation message 'chunk_msg' may contain a counter - if chunk_index
    is specified, then the correspnding index in chunk_msg will be incremented
    on each continuation.
    """
    text = textin(string)
    pad = [00]
    provisional = msg + text
    difference = limit - len(provisional) 
    if ( difference >= 2 ):
        return [ provisional + (difference * pad)]
    elif chunk_msg:
        head = provisional[0:limit]
        tail = chunk_msg + provisional[limit:]
        if chunk_index:
            chunk_msg[chunk_index] += 1
        return [ head ] + make_chunk(tail,chunk_msg,limit=limit,chunk_index=chunk_index)

def chunktest(msg, chunk_msg, string, limit=16, chunk_index=2):
    """
    >>> chunktest([1,1,1],[2,2],"testing something longer",9,1)
    01 01 01 74 65 73 74 69 6e
    02 02 67 20 73 6f 6d 65 74
    02 03 68 69 6e 67 20 6c 6f
    02 04 6e 67 65 72 00 00 00
    """
    msgs = make_chunk(msg, chunk_msg, string, limit, chunk_index)
    for line in msgs:
        print(" ".join(["%02x"%x for x in line]))

def hexin(instr):
    """converts a string or list of strings into commands"""
    for cmd in instr.split(","):
        yield [int(x, 16) for x in cmd.split(" ") if x]

def jsend(dat, asc=None):
    """just send. and print."""
    inhibitraw = False
    try:
        if interpret:
            inhibitraw = interpret(dat)
    except Exception as e:
        print(f"!  Error \"{e}\" doing (experimental) interpretation, just ignore.")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("!  "+traceback.format_tb(exc_traceback, limit=2)[1])

    if not inhibitraw:
        xprint(dat, ">> ", asc)
    EP.write(dat)

def jread(ll, delay=None, asc=None, silent=False):
    """just read <ll bytes>, optionally waiting <delay seconds> first."""
    inhibitraw = False
    if delay:
        time.sleep(delay)
    #acc = []
    out = REP.read(ll)
    while out:
        #acc += out
        try:
            if interpret:
                inhibitraw = interpret(out)
        except Exception as e:
            print(f"!  Error {e} doing (experimental) interpretation, just ignore.", file=sys.stderr)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("!  "+traceback.format_tb(exc_traceback, limit=2)[1], file=sys.stderr)

        if not (silent or inhibitraw):
            xprint(out, " < ", asc)
        out = REP.read(ll)
    if not silent:
        sys.stdout.flush()
    #return acc

def send(dat):
    """sends data and reads a max. of 40 bytes back."""
    jread(32)
    jsend(dat)

def expect(dat, matchspec):
    """
    sends data, reads data back expecting a particular response
    """
    out = REP.read(32) # discard this
    EP.write(dat)
    time.sleep(0.5)
    out = REP.read(32) # keep this
    matched = False
    while out:
        if match_bytes(out, matchspec):
            interpret(out)
            matched = True
        out = REP.read(32)
    sys.stdout.flush()
    return matched

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
    #if type(vol) == str:
    #    vol = int(vol,16)
    return int(hex(vol >> 3),16)
    #return int(vol,16)/8

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
    except (IOError, NameError) as err:
        print(f'Loading encountered error "{err}"',file=sys.stderr)
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
                jread(32, 0.2)
    elif "send" in argv[1:] and len(argv) > 2:
        for arg in argv[2:]:
            for x in hexin(arg):
                send(x)
                jread(32, 0.2)
                jread(32, 0.2)
    elif 'expect' in argv[1:] and len(argv) > 3:
        for arg in argv[2:-1]:
            for x in hexin(arg):
                if expect(make_out_header(x),argv[-1]):
                    return False # equivalent of exit(0)
        return True # equivalent of exit(1)
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
    exit(run(sys.argv[1:]))
