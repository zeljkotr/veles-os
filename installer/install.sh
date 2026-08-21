cat > ~/veles-os/installer/install.sh << 'EOF'
#!/bin/sh
# VELES OS Installer Wrapper

set -eu

echo "========================================"
echo "           VELES OS INSTALLER"
echo "========================================"
echo

# Python je u /newroot (mount-ovan SquashFS)
if [ ! -x /newroot/opt/veles/.venv/bin/python ]; then
    echo "ERROR: VELES Python runtime not found!"
    echo
    exec /bin/sh
fi

# Pokreni installer sa /newroot kao root
exec /newroot/opt/veles/.venv/bin/python \
    /newroot/installer/image/installer.py
EOF

chmod +x ~/veles-os/installer/install.sh