# pclk-mn10
Cross-platform PCLK-MN10 USB device control.

This project isn't a driver as such, but it _does_ contain enough to control some hi-fi equipment, when
connected appropriately to a PCLK device, for example turning it on or off!
I intend to map as many functions of the link as is useful to me (and others, if they care to help) until I get bored.
I do not intend for this to become well-written software at any stage(!)
Despite huge gaps between updates, this is likely to continue to be updated for as long as I still have working PCLK equipment.

Requirements:
 - Python 3.x (tested on 3.6+)
 - PyUSB >= 2.x
 - libusb >= 1.0.recent
 - An OS with USB support that run all of the above:
   * Linux should work out of the box with `libusb`
   * MacOS might also require `libusb`, probably from `brew`
   * Windows WFM with the magic of Zadig / libusbK: https://zadig.akeo.ie/

Additional requirements, if you want the software to actually do anything:
 - A PCLK-MN10, PCLK-MN10a or PCLK-MN20.  Possibly also known as a CAV-MN10 (and if you have a spare, please let me know!)
 - A Sony hifi / MiniDisc / audio device compatible with the above such as the DHC-MD595 (also possibly MDS-PC3, or one of a handful of circa 2001 MD-only decks)
 - or, for the very brave, utterly untested (by me)... any Sony hi-fi device with Control-I functionality, since it would appear that the PC-LINK port is essentially a Control-I port with power control!

What this will never control:
 - transfer of audio data (one way or the other) - these devices all handle MD contents as a separate audio stream (which can be analogue or digital!) and 
   there is no in-band audio pathway whatsoever.
 - NetMD devices (they're entirely different and covered by the likes of the excellent https://wiki.physik.fu-berlin.de/linux-minidisc/doku.php / https://github.com/AlexanderS/linux-minidisc)
 - Connection without a PCLK-MN10 - but that's OK... you can now build your own! https://github.com/Sir68k/pclink-i2c

What it's possible this could do in future, but probably won't unless I find some in a junk sale:
 - use of hardware like the [PCLK-PX1/PX2/PX3](https://www.minidisc.wiki/accessories/pclink/pclk-px1) in place of the MN10, and with some older pre-PCLK-MN10 hardware - but this would require testing with equipment I don't have.

As this project is more of a journey of understanding than a product of any sort, please see the [wiki](https://github.com/4gra/pclk-mn10/wiki) for more details / work in progress.
