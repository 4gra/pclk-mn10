#!/usr/bin/python3
from stub import *

# { pattern: function }
# add with @command
MATCHES = {
}

for cmdname in load_commands():
    try:
        cmdstr = commands[cmdname].replace('$1','??').replace('$2','??')
        if 'verbatim' in cmdstr:
            cmdstr = cmdstr.replace('verbatim','')
        else:
            cmdstr = '?? ?? 60 ' + cmdstr
        if cmdstr and not "--" in cmdstr:
            MATCHES[cmdstr.strip()] = lambda msg: print(f">> {cmdname}: "+(" ".join([f"{m:02x}" for m in msg])))
    except:
        print(f"error importing {cmdname}, skipping")


def pfprint(msg, prefix=" "):
    print(f"{prefix}{msg}")

# ---
# add command to the match table
# TODO add more matches (devtype, etc.)
def command(pattern=None, typ=None):
    if pattern is None and typ is not None:
        pattern = f'?? 00 {typ}'
    def decorate(func):
        if pattern is not None:
            #add_match(pattern, func)
            MATCHES[pattern] = func
        return func
    return decorate
# ---

DEVNAMES = {
    0xC0: 'amp?',
    0x90: 'CD',
    0xB0: 'MD',
    0x60: 'controller',
}

ERR_STRINGS={
    0x0e: 'invalid parameters?',
    0x0f: 'invalid command?'
}


@command('05 ?? 12')
def playback_event(msg):
    device= msg[2] & 0xf7
    events = {
        0x00: 'PLAY',
        0x01: 'STOP',
        0x02: 'PAUSE',
        0x03: 'EJECT',
        0xd8: 'POWEROFF',
        0xf0: 'POWERON'
        # 0xd8, 0xf0, 0xef, 0xf0: part of shutdown?
    }
    ename = events[msg[4]] if msg[4] in events else f'UNKNOWN ({msg[4]:02x})'
    #pfprint(f"+ {ename} event from {device:02x}")
    return "+ {ename} event from {device:02x}"

@command('?? 00 ?? ?? 0e')
@command('?? 00 ?? ?? 0f')
def error_output(msg):
    typ = msg[4]
    ecmd = f' for command {msg[5]:02x}' if len(msg) > 5 else ''
    emsg = ERR_STRINGS[typ] if typ in ERR_STRINGS else 'Unknown {typ:02x}.'
    #pfprint(f"ERROR {typ:02x} @ {addr[0]:02x}:{addr[1]:02x} ({emsg}) {ecmd}")
    return f"ERROR {typ:02x} @ {addr[0]:02x}:{addr[1]:02x} ({emsg}) {ecmd}"

# TODO: check if from b0 or 90, figure out yet what '12' means
@command('?? ?? 12 71')
def media_change(msg):
    media = (0x01 & msg[8])
    wp = (0x01 & msg[14])
    disc = msg[7]
    (tracks, hrs, mins, secs) = (msg[9:13])
    pfprint(f"Media change. Disc inserted: {'yes' if media else 'no'}, Write-protected: {'yes' if wp else ('no' if media else 'n/a')}.")
    if (media):
        pfprint(f"Disc {disc} has {msg[9]:02} tracks, {hrs:01}:{mins:02}:{secs:02} duration.")
    #pfprint("-- -- -- -- -- -- 06 -- -- -- -- -- -- 13 -- 15 16 --")
    return True

# 05 00 18 c8 c2 01
@command('?? ?? 1? c? c2')
def dbfb_event(msg):
    dbfb = msg[5] & 0x01
    pfprint(f"DBFB is now {dbfb}")
    return True

@command('06 ?? 1? c? c9')
def amp_feature(msg):
    # < 06 00 18 cb c9 02 03
    # TODO< followed by this, what is this?
    # < 16 00 18 c9 c1 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    types = {
        0x02: 'EQ',
    }
    param = types[msg[5]] if msg[5] in types else 'unknown ({msg[5]:02x})'
    value = msg[6] 
    pfprint(f"Amp feature '{param}' is now set to {value:02}.")

# TODO: check if from b0 (12, 70) or 90 (10, 70), figure out what '10 / 12' mean, and
#       if (0x18, 0x70) tells us what subsystems we can query?
@command('?? ?? 10 ?? 70')
@command('?? ?? 12 ?? 70')
def media_status(msg):
    (devid, disc, track) = msg[5:8]
    # bit mask
    play_modes = {
        0x00: 'None',
        0x01: 'Repeat All',
        0x02: 'Repeat 1',
        0x08: 'Shuffle',
        0x10: 'Program',
    }
    # list
    rec_modes = {
        0x00: 'STEREO',
        0x01: 'MONO',
        0x02: 'MD2',
        0x03: 'MD4',
    }
    # list? mask?
    play_state = {
        0x00: 'stop',
        0x01: 'play',
        0x02: 'pause',
        #0x03: '(no disc)',
        0x04: 'record',
        #0x07: '(DAC)'
    }
    rec_flags = {
        0x01: 'Smart Space',
        0x02: 'L.SYNC',
        0x10: 'LP Stamp',
    }
    rec_source = {
        0x08: 'ANALOG',
        0x10: 'DIGITAL',
    }

    play_set = [name for (bits,name) in play_state.items() if (bits & msg[9])] or ['stopped']
    #playstate = play_state[msg[9]] if msg[9] in play_state else 'unknown'
    play_mode = [name for (bits,name) in play_modes.items() if (bits & msg[12])] or ['none']
    rec_flags_set = []
    recmode = None
    rec_src = []
    try:
        rec_flags_set = [name for (bits,name) in rec_flags.items() if (bits & msg[13])] or ['none']
        recmode = rec_modes[msg[14]] if msg[14] in rec_modes else 'unknown'
        rec_src = [name for (bits,name) in rec_source.items() if (bits & msg[15])] or ['unavailable']
    except IndexError:
        pfprint(f"Not a recordable medium I suppose. TODO, detect this from the message.")
    
    playstate = ", ".join(play_set)
    playmodes = ", ".join(play_mode)
    recflags  = ", ".join(rec_flags_set)
    recsource = ", ".join(rec_src)

    pfprint(f"Status for id {devid}, disc {disc}{f', track {track}' if track else ' (disc)'}:")
    pfprint(f"Playback: {playstate}, modes: {playmodes}.")
    pfprint(f"Rec Mode: {recmode}, source {recsource}, flags: {recflags}.")
    pfprint(f"Byte 8 (Loading?) {msg[8]:02x} ({msg[8]:03})")
    if len(msg) > 15:
        pfprint(f"Byte 16? {msg[16]:02x} ?")
    #pfprint("-- -- -- -- -- -- -- -- 08 -- 10 11 -- -- -- -- 16 --")

@command('?? 00 12 ?? c0')
def play_mode(msg):
    device= msg[2] & 0xf7
    play_modes = {
        0x00: 'None',
        0x04: '1',
        0x08: 'Repeat',
        0x20: 'Shuffle',
        0x10: 'Program',
    }
    play_mode = [name for (bits,name) in play_modes.items() if (bits & msg[8])] or ['none']
    playmodes = ", ".join(play_mode)

    pfprint(f"c0 (LCD?) Status for {device} ... TODO") #id {devid}, disc {disc}{f', track {track}' if track else ' (disc)'}:")
    pfprint(f"Playback: TODO, modes: {playmodes}.")


@command('?? 00 18 ?? 70 80')
@command('?? 00 18 ?? 70 81')
def freq_change(msg):
    ## FREQUENCY change
    # < 09 00 18 c9 70 81 03 09 03 e7
    #< 09 00 18 c9 70 80 14 08 22 2e
    tband = ('AM','kHz') if msg[5] == 0x81 else ('FM','MHz')
    preset = msg[6]
    bandmaybe = msg[7]
    freq = (msg[8] << 8) + msg[9]
    if tband[0] == 'FM':
        freq = freq / 100
    pfprint(f"Tuner {tband[0]} frequency change: preset {preset:02}, freq {freq:03}{tband[1]}, band?? {bandmaybe:02x}")
    return True


@command('?? 00 18 ?? 70')
def input_change(msg):
    ## INPUT change
    #< 09 00 18 c9 70 81 04 09 05 7c
    sources = {
        0x02: 'CD', 0x04: 'MD', 0x00: 'TUNER', 0x0B: 'ANALOG', 
        0x08: 'OPTICAL', 0x05: 'TAPE'
    }
    src =''
    try:
        src=sources[msg[5]]
    except KeyError:
        src=f'Unknown {msg[5]:02x}'
    change="CHANGED" if msg[7] == 3 else "not changed"
    pfprint(f"Input source {src}, {change}")

# @command('0a 00 12 ?? 50')
@command('0a 00 ?? ?? 50')
def track_info(msg):
    # < 0a 00 12 b8 50 00 01 01 00 2e 09
    #TX|.. .. .. ..  P .. .. .. ..  . ..
    (devid, disc, track, hrs, mins, secs) = (msg[5:11])
    pfprint(f'Track info: id {devid}, disc {disc}, track {track:01}, {hrs:01}:{mins:02}:{secs:02}.')

@command('?? 00 ?? ?? 51')
def timing_info(msg):
    (unkn, hrs, mins, secs) = (msg[5:9])
    pfprint(f'Playback timing update 0x51: {hrs:01}:{mins:02}:{secs:02}')
    if unkn != 00:
        pfprint(f"Unknown byte 5 has value {unkn:02x} ({unkn:02}")

@command('?? 00 ?? ?? 63')
def clock_update(msg):
    ##| Message 63, addr 18:ca, Length 0d
    # | Device c2 is amp?#2, << IN, address 18
    # | 01 ff ff ff ff 00 25 0c 06
    # < 0d 00 18 ca 63 01 ff ff ff ff 00 25 0c 06
    #TX|.. .. .. ..  c .. .. .. .. .. ..  % .. ..
    (hrs, mins, secs, unkn) = (msg[10:14])
    pfprint(f'Clock: {msg[5]:02x}: {hrs:02}:{mins:02}:{secs:02} {unkn:02x}?')
    return True

@command('?? 00 ?? ?? 13')
def iamhere(msg):
    pfprint(f"Yes, I am here!")

@command('04 00 ?? c? c7')
def vol_enquiry(msg):
    # < 05 00 18 c8 c7 70
    if length == 0x04:
        pfprint(f"Volume Enquiry?")
        return True

@command('05 00 ?? c? c7')
def vol_change(msg):
    vol = msg[5] >> 3
    pfprint(f"Volume update: {vol:02}")
    return True


@command('?? 00 ?? c8 e0')
def display_update(msg):
# < 12 00 18 c8 e0 4f 50 54 49 43 41 4c 20 49 4e 31 34 00 00
    text="".join([ dtext(x) for x in msg[5:15] ])
    #seq = "{:02x}".format(int(msg[15:]))
    seq = ", ".join([ f"{m:02x}" for m in msg[15:16] ])
    pfprint(f"Display update: \"{text}\" seq {seq}")
    if len(msg[16:]):
        pfprint(" ".join("{:02x}".format(x) for x in msg[16:]))
    #pfprint("=[  end  ]=" + "="*60 + "\n")

#    elif type == [0x18, 0xc1]:
#        pfprint("Another display update?")
#        text="".join([ dtext(x) for x in msg[9:] ])
#        pfprint("Display update: \"{}\"".format(text))
#
#        # | Message 18,c1, addr 00:c8, Length 16
#        # | 00 04 00 ff 53 54 41 4e 44 42 59 00 00 00 00 00 00 00
#        # < 16 00 18 c8 c1 00 04 00 ff 53 54 41 4e 44 42 59 00 00 00 00 00 00 00
#        #TX|.. .. .. .. .. .. .. .. ..  S  T  A  N  D  B  Y .. .. .. .. .. .. ..
#        # | Message 18,c1, addr 00:c8, Length 16
#        # | 00 04 00 ff 20 20 20 20 20 20 20 00 00 00 00 00 00 00
#        # < 16 00 18 c8 c1 00 04 00 ff 20 20 20 20 20 20 20 00 00 00 00 00 00 00
#        #TX|.. .. .. .. .. .. .. .. ..                      .. .. .. .. .. .. ..
#        # | Message 18,c1, addr 00:c8, Length 16
#        # | 00 04 00 ff 53 54 41 4e 44 42 59 00 00 00 00 00 00 00
#        # < 16 00 18 c8 c1 00 04 00 ff 53 54 41 4e 44 42 59 00 00 00 00 00 00 00
#        #TX|.. .. .. .. .. .. .. .. ..  S  T  A  N  D  B  Y .. .. .. .. .. .. ..
#        # | Message 18,c1, addr 00:c8, Length 16
#        # | 00 04 00 ff 20 20 20 20 20 20 20 00 00 00 00 00 00 00
#        # < 16 00 18 c8 c1 00 04 00 ff 20 20 20 20 20 20 20 00 00 00 00 00 00 00
#        #TX|.. .. .. .. .. .. .. .. ..                      .. .. .. .. .. .. ..
#

@command('?? 00 ?? ?? e2')
@command('?? 00 ?? ?? e0')
def display_update(msg):
    #elif typ[0] in (0x10, 0x12) and 
    #elif typ in (0xe0, 0xe2): # (and msg[3] != 0xc8):
    typ = msg[4]
    page = msg[5]
    text = []
    sep = True
    ix = 0
    for ix, byte in enumerate(msg[5:]):
        if byte == 00:
            sep = True
        elif byte == 0x02:
            text += ':'
            sep = True
        elif byte == 0xff:
            break
        elif sep:
            sep = False
            text += dtext(byte)
        else:
            text[-1] += dtext(byte)

    alltext = "|".join(text)
    pfprint(f"Display update {typ:02x}#{page:01}: [{alltext}]")
    #pfprint("   (Time updates Disk/Trk/MM/SS, Clock HH/MM)")
    # print the remainder, if unexplained
    rest=""
    for byte in msg[(5+ix):]:
        if byte != 0xff:
            rest+= f"{byte:02x} ({byte:02}) "
    if rest:
        pfprint(f"Mystery last bytes: {rest}")
    #return True # inhibit raw hex

    # Before CD playback
    # < 17 00 10 98 e0 31 00 34 31 00 00 00 00 00 00 20 36 39 00 31 35 00 03 00
    #TX|.. .. .. .. ..  1 ..  4  1 .. .. .. .. .. ..     6  9 ..  1  5 .. .. ..

    # From OPTICAL 
    # | Message 18,e0, addr 00:03, Length 0e
    # < 0e 00 18 03 e0 00 01 08 00 ff f0 ff ff ff ff
    #TX|.. .. .. .. .. .. .. .. .. .. .. .. .. .. ..
    # < 0e 00 18 03 e0 00 01 08 00 ff ff ff ff ff ff
    #TX|.. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

    # From MD playback
    # < 14 00 12 b8 e0 31 00 34 00 00 00 00 31 00 00 00 30 30 00 a3 00
    #TX|.. .. .. .. ..  1 ..  4 .. .. .. ..  1 .. .. ..  0  0 .. .. ..

    # Clock time ticker
    #  < 14 00 18 ca e2 01 20 20 20 20 20 20 20 20 06 31 32 02 31 32 ff
    # TX|.. .. .. .. .. ..                         ..  1  2 ..  1  2 ..
    #  < 14 00 18 ca e2 01 20 20 20 20 20 20 20 20 00 31 32 00 33 35 ff
    # TX|.. .. .. .. .. ..                         ..  1  2 ..  3  5 ..

    # Another 18 ca update
    #  < 0d 00 18 ca 63 01 ff ff ff ff 0c 23 26 00
    # TX|.. .. .. ..  c .. .. .. .. .. ..  #  & ..



def interpret(msg, prefix=" | ", matchspec=None):
    """
    More experiental work at understanding the returned messages.

    dat: bytes to interpret
    prefix: prepend an ASCII prefix to printed output
    match:  return only details matching the byte spec given
              e.g. '?? ?? 1? c? 70'
            if the data doesn't match, return quietly
    """
    if matchspec and not match_bytes(msg, matchspec):
        return False # inhibit hex

    pfprint = lambda x : print(prefix+x)

    if msg == [0x00, 0x60, 0x00]:
        pfprint("GLOBAL POWER ON message")
        return
    elif len(msg) > 0 and len(msg) < 4:
        print()
        pfprint("UNKNOWN SHORT Message %s" % ' '.join(["{:02x}".format(s) for s in msg]))
        return
    else:
        length=msg[0]
        typ = msg[4]
        addr = msg[2:4]
        # e.g. CD players start at 0x90 + ID bits (0x01, 0x02, ..) +  reply bit (0x08)
        device, devtype, devid = addr[1] & 0xf7, addr[1] & 0xf0, addr[1] & 0x07
        inbound = addr[1] & 0x08
        devname = f"{DEVNAMES[devtype] if devtype in DEVNAMES else 'unknown'}#{devid:01}"

        # ------------ SELECTION BEGINS ------------------------
        for spec in MATCHES:
            #pfprint(f'trying to match {spec} = {msg}?')
            if match_bytes(msg, spec, full=True):
                handler = MATCHES[spec]
                #print(f"--> {handler.__name__} MATCHED <--")
                result = MATCHES[spec](msg)
                #print(f"--> {handler.__name__}: {result or 'None'} <--")
                return True

    # ------------ GENERAL REMARKS ------------------------
    print("")
    std  = prefix+f"Message {typ:02x}, addr {addr[0]:02x}:{addr[1]:02x}, Length {length:02x}\n"
    std += prefix+f"Device {device:02x} is {devname}, {'<< IN' if inbound else '> OUT'}, address {addr[0]:02x}"

    #elif len(msg) > 5 and chunk > 0x00:
    #    pfprint(f"*** This command is a continuation ({chunk}) ***")

    print(std)
    pfprint("Not yet interpreted.")
    if len(msg[5:]):
        pfprint(" ".join("{:02x}".format(x) for x in msg[5:]))


# Allow us to work stuff out manually
if __name__ == '__main__':
    from sys import argv
    for aa in argv[1:]:
        for cmd in hexin(aa):
            interpret(cmd, prefix="")
