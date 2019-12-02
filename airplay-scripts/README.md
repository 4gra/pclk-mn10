Some examples of scripts that could be used by, e.g. a (sh)airplay server.
Add all, any or indeed none of these to your shairport-sync.conf:

    run_this_before_play_begins = "/path/to/pclk-mn10/airplay-scripts/on"; 
    run_this_after_play_ends    = "/path/to/pclk-mn10/airplay-scripts/off"; 
    run_this_when_volume_is_set = "/path/to/pclk-mn10/control volsp ";  // note trailing space

