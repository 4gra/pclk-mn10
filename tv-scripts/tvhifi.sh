#!/bin/bash
# Let your MD595 device become a soundbar, whatever that is
# Designed for a Panasonic Viera 2015-ish series TV returning volume 0-100
# (uses hacky homebrew curl-powered SOAP commands; not included)

# command to return volume integer, 0-100
volcmd="${HOME}/TV/SOAP/getvol"
# commad to return mute status as 1 (muted) or 0 (noise-makey)
mutecmd="${HOME}/TV/SOAP/getmute"
# path to the pclk control command
pclk="$HOME/pclk-mn10"
# MD595 source connected to the TV (likely OPTICAL, TAPE or ANALOG)
tvsource="OPTICAL"
# slow loop speed, in seconds (when TV has been off)
slowloop=120
# fast loop speed, in seconds (when TV is on)
fastloop=1

while true; do 
    OLDVOL="$VOL$MUTE"
    VOL=$(${volcmd})
    MUTE=$(${mutecmd})
    if [[ $? == 0 && -n $VOL ]]; then
        if [[ $OLDVOL != $VOL$MUTE ]]; then
            if [[ $MUTE == 1 ]]; then
                ${pclk}/control mute
            else
                ${pclk}/control vol $[$VOL*4/10+5]
            fi
        else
            sleep ${fastloop}
        fi
    else 
        VOL=""
        sleep ${slowloop}
    fi
    if [[ -z $OLDVOL && -n $VOL ]]; then
        ${pclk}/on ${tvsource}
    elif [[ -n $OLDVOL && -z $VOL ]]; then
        ${pclk}/off ${tvsource}
    fi
done
