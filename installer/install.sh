#!/bin/sh

set -eu

echo "========================================"
echo "           VELES OS INSTALLER"
echo "========================================"
echo

if [ ! -x /newroot/opt/veles/.venv/bin/python ]; then
    echo "ERROR: VELES Python runtime not found!"
    echo
    exec /bin/sh
fi

if [ ! -f /newroot/installer/image/installer.py ]; then
    echo "ERROR: VELES installer not found!"
    echo
    exec /bin/sh
fi

exec /newroot/opt/veles/.venv/bin/python \
    /newroot/installer/image/installer.py