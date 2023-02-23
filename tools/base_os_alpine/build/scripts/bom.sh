#! /bin/sh
# Extract packages from Alpine linux
# a,alpinelinux,musl,1.1.15,r6,alpine_linux_3.3,http://www.musl-libc.org/
# The exclude argument blocks entry to be added in output

exec 2<&-


# Extract vendor and platform from /etc/os-release
# ID=alpine
# VERSION_ID=3.11.6

alpine_version=`cat /etc/os-release | grep VERSION_ID | awk -F= '{print $NF}' | awk -F. '{printf "%s.%s\n", $1,$2}'`
vendor=`cat /etc/os-release | grep \^ID | awk -F= '{print $NF}'`

platform=${vendor}_linux_${alpine_version}



LIST=`apk info  | grep -v WARNING`
for p in $LIST
 do
  LONG_VERSION=`apk info $p 2> /dev/null | grep  description | awk '{print $1}'`
  VER_REV=`echo $LONG_VERSION | sed "s/^\$p-//"`
  VERSION=`echo $VER_REV | awk -F\- '{print $1}'`
  REVISION=`echo $VER_REV | awk -F\- '{print $2}'`
  PACKAGE=$p
  URL=`apk info $p 2> /dev/null | grep '://' `
  echo "a,$vendor,$PACKAGE,$VERSION,$REVISION,$platform,$URL"
 done

if test -x /usr/local/bin/bom_extra.sh ; then
        sh /usr/local/bin/bom_extra.sh
fi





