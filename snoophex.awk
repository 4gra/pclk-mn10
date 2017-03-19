#!/usr/bin/env awk -f
# Strips metadata from the output of Benoit Papillault's usbsnoop 
#  to show simple, directional hex strings. 
#
# Copyright (C) 2017, https://github.com/4gra/pclk-mn10
# This program comes with ABSOLUTELY NO WARRANTY; for details see included LICENCE.
# This is free software, and you are welcome to redistribute it under certain
# conditions; view the included file LICENCE for details.
#
# Variables:
#  INDENT   : controls line prefix 
#   for example -v INDENT="    "
#   to produce markdown-friendly preformatted output.
#  TIMES    : print (approx) timestamps before data
#  ASCII    : print ASCII (32 <= chr < 128) beneath hex values
#
# (not implmemented yet...)
#  BINBYTES : comma-separated list of bytes to render as binary
#  DECBYTES : comma-separated list of bytes to render as decimal
#
function hextoasc(h,no,i,x,v){
  for(i=1;i<=length(h);++i){
    x=index("0123456789abcdef",substr(h,i,1));
    v=(16*v)+x-1;
  }
  if(v < 128 && v >= 32) return sprintf(" %c",v);
  return no;
}
BEGIN{printf INDENT"# >> is to device; < is from device. -<- are control flows.";}
TIMES && /^\[[0-9]+ ms\]/{TIME=sprintf("%7.2f",substr($1,2)/1000);}
/URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER/{TYP="DATA";SP=" ";}
/IRP_MJ_INTERNAL_DEVICE_CONTROL/{TYP="CTRL";SP="-";}
/DIRECTION_IN/{	DIR="\n"INDENT SP TIME SP "<" SP;}
/DIRECTION_OUT/{DIR="\n"INDENT SP TIME SP ">>";}
/00:/{
  if (ASCII && hex) { print hex; hex=""; }
  $1=DIR;printf;
  if(ASCII) { hex=$1; for(i = 2; i <= NF; i++) hex=hex" "hextoasc($i,"  "); }
}
/[^0]0:/{
  $1="";printf;
  if(ASCII) { hex=hex $1; for(i = 2; i <= NF; i++) hex=hex" "hextoasc($i,"  "); }
}
END{print "";}
