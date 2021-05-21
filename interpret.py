#!/usr/bin/python3

def dtext(word):
    """Silly ASCII printout helper"""
    return "%1s"%chr(word) if (word >= 0x20 and word < 127) else '' if word == 0 else '?'

def interpret(dat, prefix=" | "):
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
        print("\n"+prefix+"SHORT Message %s" % ' '.join(["{:02x}".format(s) for s in msg]))
        return

    length=msg[0]

    # message type is #4
    # address is built up of #2 and #3, but I don't know what #2 really means.

    # typ[0] => addr[0]; typ[1] => typ
    typ = msg[4]
    addr = msg[2:4]
    device, devtype, devid = addr[1] & 0xf7, addr[1] & 0xf0, addr[1] & 0x07
    inbound = addr[1] & 0x08
    chunk = msg[5] if len(msg) > 5 else None

    # Select a command of interest
    #if not (typ == 0x50 and addr[0] == 0x12):
    #    return 

    # ------------ GENERAL REMARKS ------------------------
    print("\n"+prefix+f"Message {typ:02x}, addr {addr[0]:02x}:{addr[1]:02x}, Length {length:02x}")
    print(prefix+f"Device {device:02x}, {'inbound' if inbound else 'outbound'}, address {addr[0]:02x}")

    if len(msg) == 5 and addr[0] == 0x12:
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
        print(prefix+f"+ {ename} event from {device:02x}")

    #elif len(msg) > 5 and chunk > 0x00:
    #    print(prefix+f"*** This command is a continuation ({chunk}) ***")

    # ------------ SELECTION BEGINS ------------------------
    if typ in (0x0e, 0x0f):
        errs={
            0x0e: 'invalid parameters?',
            0x0f: 'invalid command?'
        }
        ecmd = f' for command {msg[5]:02x}' if len(msg) > 5 else ''
        emsg = errs[typ] if typ in errs else 'Unknown {typ:02x}.'
        print(prefix+f"ERROR {typ:02x} @ {addr[0]:02x}:{addr[1]:02x} ({emsg}) {ecmd}")

    # TODO: check if from b0 or 90, figure out yet what '12' means
    elif typ == [0x12, 0x71]:
        media = (0x01 & msg[8])
        wp = (0x01 & msg[14])
        disc = msg[7]
        (tracks, hrs, mins, secs) = (msg[9:13])
        print(prefix+f"Media change. Disc inserted: {'yes' if media else 'no'}, Write-protected: {'yes' if wp else ('no' if media else 'n/a')}.")
        if (media):
            print(prefix+f"Disc {disc} has {msg[9]:02} tracks, {hrs:01}:{mins:02}:{secs:02} duration.")
        print(prefix+"-- -- -- -- -- -- 06 -- -- -- -- -- -- 13 -- 15 16 --")

    # TODO: check if from b0 (12, 70) or 90 (10, 70), figure out what '10 / 12' mean, and
    #       if (0x18, 0x70) tells us what subsystems we can query?
    elif addr[0] in (0x10, 0x12) and typ == 0x70:
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
            print(prefix+f"Not a recordable medium I suppose. TODO, detect this from the message.")
        
        playstate = ", ".join(play_set)
        playmodes = ", ".join(play_mode)
        recflags  = ", ".join(rec_flags_set)
        recsource = ", ".join(rec_src)

        print(prefix+f"Status for id {devid}, disc {disc}{f', track {track}' if track else ' (disc)'}:")
        print(prefix+f"Playback: {playstate}, modes: {playmodes}.")
        print(prefix+f"Rec Mode: {recmode}, source {recsource}, flags: {recflags}.")
        print(prefix+f"Byte 8 (Loading?) {msg[8]:02x} ({msg[8]:03})")
        if len(msg) > 15:
            print(prefix+f"Byte 16? {msg[16]:02x} ?")
        print(prefix+"-- -- -- -- -- -- -- -- 08 -- 10 11 -- -- -- -- 16 --")

    elif typ == 0xc0 and addr[0] == 0x12:
        play_modes = {
            0x00: 'None',
            0x04: '1',
            0x08: 'Repeat',
            0x20: 'Shuffle',
            0x10: 'Program',
        }
        play_mode = [name for (bits,name) in play_modes.items() if (bits & msg[8])] or ['none']
        playmodes = ", ".join(play_mode)

        print(prefix+f"c0 (LCD?) Status for {device} ... TODO") #id {devid}, disc {disc}{f', track {track}' if track else ' (disc)'}:")
        print(prefix+f"Playback: TODO, modes: {playmodes}.")


    elif typ == 0x70 and addr[0] == 0x18:
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
        print(prefix+f"Input source {src}, {change}")

    elif typ == 0x50: # and addr[0] == 0x12:
        # < 0a 00 12 b8 50 00 01 01 00 2e 09
        #TX|.. .. .. ..  P .. .. .. ..  . ..
        (devid, disc, track, hrs, mins, secs) = (msg[5:11])
        print(prefix+f'Track info: id {devid}, disc {disc}, track {track:01}, {hrs:01}:{mins:02}:{secs:02}.')

    elif typ == 0x13:
        print(prefix+f"Yes, I am here!")

    # < 05 00 18 c8 c7 70
    elif typ == 0xc7 and addr[0] == 0x18:
        print(prefix+"Reply to display request?  ("+" ".join("{:02x}".format(x) for x in msg[5:])+")")

    # < 12 00 18 c8 e0 4f 50 54 49 43 41 4c 20 49 4e 31 34 00 00
    elif typ == 0xe0 and addr[1] == 0xc8:
        text="".join([ dtext(x) for x in msg[5:15] ])
        #seq = "{:02x}".format(int(msg[15:]))
        seq = msg[15:16]
        print(prefix+"Display update: \"{}\" seq {}".format(text, seq))
        if len(msg[16:]):
            print(prefix+" ".join("{:02x}".format(x) for x in msg[16:]))
        #print(prefix+"=[  end  ]=" + "="*60 + "\n")

#    elif type == [0x18, 0xc1]:
#        print(prefix+"Another display update?")
#        text="".join([ dtext(x) for x in msg[9:] ])
#        print(prefix+"Display update: \"{}\"".format(text))
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

    #elif typ[0] in (0x10, 0x12) and 
    elif typ == 0xe0: # (and msg[3] != 0xc8):
        seq = msg[15:16]
        print(prefix+"ASCII display / time update?")

        text = []
        sep = True
        for byte in msg[5:]:
            if byte == 00:
                sep = True
            elif sep:
                sep = False
                text += dtext(byte)
            else:
                text[-1] += dtext(byte)

        print(prefix+"["+"|".join(text)+"]")
        for byte in msg[-2:]:
            print(prefix+f"Remainder: {byte:02x} ({byte:02})...")

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

    elif len(msg[5:]):
        print(prefix+"Not yet interpreted.")
        print(prefix+" ".join("{:02x}".format(x) for x in msg[5:]))
        #print(prefix+"=[  end  ]=" + "="*60 + "\n")
