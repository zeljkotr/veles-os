#!/bin/sh
# VELES OS Installer

set -eu

echo "========================================"
echo "           VELES OS INSTALLER"
echo "========================================"
echo

# Mount SquashFS da dobijemo Python
mkdir -p /run/rootfs
mount -t squashfs -o ro /veles/rootfs.squashfs /run/rootfs

# Pokreni Python installer
exec /run/rootfs/opt/veles/.venv/bin/python \
    /run/rootfs/installer/image/installer.py
