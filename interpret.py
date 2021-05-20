#!/usr/bin/python3

def dtext(word):
    """Silly ASCII printout helper"""
    return "%1s"%chr(word) if (word > 31 and word < 127) else '' if word == 0 else '?'

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
    typ=[msg[2]] + [msg[4]]
    print("\n"+prefix+"Message {:02x},{:02x}, addr {:02x}:{:02x}, Length {:02x}".format(
        typ[0], typ[1], msg[1], msg[3], length)
    )
    if typ[1] in (0x0e, 0x0f):
        errs={
            0x0e: 'invalid parameters?',
            0x0f: 'invalid command?'
        }
        ecmd = msg[5] if len(msg) > 5 else None
        print(prefix+"ERROR {:02x}{:02x} ({:s}) for command {:02x}".format(typ[0],typ[1], errs[typ[1]], ecmd))

    # TODO: check if from b0 or 90, figure out yet what '12' means
    elif typ == [0x12, 0x70] and msg[5] == 0x00:
        (disc, track) = msg[6], msg[7]
        # TODO: enum
        play_modes = {
            0x00: 'None',
            0x01: 'Repeat All',
            0x02: 'Repeat 1',
            0x08: 'Shuffle',
            0x10: 'PGM',
        }
        rec_modes = {
            0x00: 'STEREO',
            0x01: 'MONO',
            0x02: 'MD2',
            0x03: 'MD4',
        }
        play_state = {
            0x00: 'stop',
            0x01: 'play',
            0x02: 'pause',
            0x04: 'record',
        }
        rec_source = {
            0x08: 'ANALOG',
            0x10: 'DIGITAL',
        }

        play_set = [name for (bits,name) in play_state.items() if (bits & msg[9])] or ['stopped']
        play_mode = [name for (bits,name) in play_modes.items() if (bits & msg[12])] or ['none']
        rec_src = [name for (bits,name) in rec_source.items() if (bits & msg[15])] or ['unavailable']
        
        playstate = ", ".join(play_set)
        recsource = ", ".join(rec_src)
        playmodes = ", ".join(play_mode)
        recmode = rec_modes[msg[14]] if msg[14] in rec_modes else 'unknown'

        print(prefix+f"Status block: Disc {disc}, Track {track}")
        print(prefix+f"Playback State: {playstate}.")
        print(prefix+f"Play Modes: {playmodes}.")
        print(prefix+f"Rec Mode: {recmode}, source {recsource}.")
        #print(prefix+"-- -- -- -- -- 05 06 07 08 09 10 11 12 13 14 15 16 17 -- -- --")

    elif typ == [0x18, 0x70]:
        sources = {
            0x02: 'CD', 0x04: 'MD', 0x00: 'TUNER', 0x0B: 'ANALOG', 
            0x08: 'OPTICAL', 0x05: 'TAPE'
        }
        src=sources[msg[5]]
        change="CHANGED" if msg[7] == 3 else "not changed"
        print(prefix+f"Input source {src}, {change}")
        return True

    elif typ[0] == 0x13:
        print(prefix+f"Yes, I am here!")

    # < 05 00 18 c8 c7 70
    elif typ == [0x18, 0xc7]:
        print(prefix+"Reply to display request?  ("+" ".join("{:02x}".format(x) for x in msg[5:])+")")

    # < 12 00 18 c8 e0 4f 50 54 49 43 41 4c 20 49 4e 31 34 00 00
    elif typ[1] == 0xe0 and msg[3] == 0xc8:
        text="".join([ dtext(x) for x in msg[5:15] ])
        #seq = "{:02x}".format(int(msg[15:]))
        seq = msg[15:16]
        print(prefix+"Display update: \"{}\" seq {}".format(text, seq))
        if len(msg[16:]):
            print(prefix+" ".join("{:02x}".format(x) for x in msg[16:]))
        #print(prefix+"=[  end  ]=" + "="*60 + "\n")

    elif typ[1] == 0xe0 and msg[3] != 0xc8:
        seq = msg[15:16]
        print(prefix+"NOT a display update...")
        if len(msg[16:]):
            print(prefix+" ".join("{:02x}".format(x) for x in msg[16:]))

    elif len(msg[5:]):
        print(prefix+" ".join("{:02x}".format(x) for x in msg[5:]))
        #print(prefix+"=[  end  ]=" + "="*60 + "\n")
