#!/bin/sh
# Downloads simavr into tools/sim/.deps and builds the virtual device. No root needed.
# Only needed for running the tests, not for uploading to the Uno. Ubuntu/Debian only.
set -e
cd "$(dirname "$0")"
if [ ! -d .deps/root ]; then
  mkdir -p .deps/debs
  (cd .deps/debs && apt-get download simavr libsimavr2 libsimavrparts1 libsimavr-dev libelf-dev zlib1g-dev)
  for deb in .deps/debs/*.deb; do dpkg -x "$deb" .deps/root; done
fi
LIB="$PWD/.deps/root/usr/lib/x86_64-linux-gnu"
gcc -O2 -fPIC -shared -Wall -I.deps/root/usr/include -I.deps/root/usr/include/simavr harness.c \
  -L"$LIB" -lsimavr -lsimavrparts -lelf -Wl,-rpath,"$LIB" -o .deps/libharness.so
echo "Built tools/sim/.deps/libharness.so"
