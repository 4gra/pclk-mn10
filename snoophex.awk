#!/usr/bin/env awk -f
# Strips metadata from the output of Benoit Papillault's usbsnoop 
#  to show simple, directional hex strings. 
#
# Copyright (C) 2017, https://github.com/4gra/pclk-mn10
# This program comes with ABSOLUTELY NO WARRANTY; for details see included LICENCE.
# This is free software, and you are welcome to redistribute it under certain
# conditions; view the included file LICENCE for details.
#
BEGIN{printf INDENT"# >> is to device; < is from device. -<- are control flows.";}
/URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER/{TYP="DATA";SP=" ";}
/IRP_MJ_INTERNAL_DEVICE_CONTROL/{TYP="CTRL";SP="-";}
/DIRECTION_IN/{	DIR="\n"INDENT SP "<" SP;}
/DIRECTION_OUT/{DIR="\n"INDENT SP ">>";}
/00:/{$1=DIR;printf;}
/[^0]0:/{$1="";printf;}
END{print "";}
