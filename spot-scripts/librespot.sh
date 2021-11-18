#!/bin/bash
# Outline of a script which powers on/off the amp based on spotify connect inputs

# path to the pclk control command
pclk="~/pclk-mn10"

# MD595 source connected to the TV (likely OPTICAL, TAPE or ANALOG)
source="TAPE"

function track_update() {
# if you want to do something when the track name updates, here is a good place
}

case "${PLAYER_EVENT},${SINK_STATUS}" in

stop,|sink,closed)
    ${pclk}/off ${source} &
    track_update off
    ;;

start,|sink,running)
    ${pclk}/on ${source}
    track_update
    ;;

volume_set,)
    # TODO: rate limit this as it'll overwhelm the pclk
    ;;

paused,)
    track_update
    ;;

playing,)
    track_update
    ;; # don't log this

change,|preloading,)
    ;; # ignore

*)
    echo "Ignored unknown event $PLAYER_EVENT,$SINK_STATUS"
    #track_update
    ;;

esac

exit 0
