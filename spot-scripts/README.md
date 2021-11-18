Were you to install `librespot` to a raspberry pi via [raspotify](https://github.com/dtcooper/raspotify) you could launch it with defaults like:

```
OPTIONS="--emit-sink-events --onevent=/path/to/spot-scripts/librespot.sh"
```

and then Spotify Connect would turn your amp on and off, too (but only if it wasn't busy doing something else).

Neat, eh?
