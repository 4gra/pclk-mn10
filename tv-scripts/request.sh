#!/bin/bash
# Ludicrously simple way to get information from a Panasonic TV.
# Never use in an untrusted environment (which is to say, anywhere).
# Usage requires a bit of interpretation I'm afraid, e.g.:
#  request.sh GetVolume | grep -oPm1 "(?<=<CurrentVolume>)[^<]+"
#  request.sh GetMute | grep -oPm1 "(?<=<CurrentMute>)[^<]+"

action=$1
[[ -z $VIERA_HOSTNAME ]] && { echo "Set VIERA_HOSTNAME before continuing"; exit 1; }

echo '
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:@ACTION@ xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
   <InstanceID>0</InstanceID>
   <Channel>Master</Channel>
  </u:@ACTION@>
 </s:Body>
</s:Envelope>' | sed -e"s/@ACTION@/$action/" | \
\
curl -s -X POST -d @- \
   -H 'Content-Type: text/xml; charset="utf-8"' \
   -H "SOAPACTION: \"urn:schemas-upnp-org:service:RenderingControl:1#$action\"" \
   http://${VIERA_HOSTNAME}:55000/dmr/control_0
