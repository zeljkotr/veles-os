#!/bin/bash
# ============================================================
# VELES-OS BUILDER - Pretvara VELES aplikaciju u Linux OS
# ============================================================

set -e

cd ~/veles-os

echo "=========================================="
echo "  🚀 VELES-OS BUILDER v1.0"
echo "  Pretvaram aplikaciju u Linux OS"
echo "=========================================="

# 1. POPRAVI ROOTFS.PY
echo "[1/8] Popravljam rootfs.py..."
sudo sed -i '1502s/.*/"usr\/share\/x11",/' installer/image/rootfs.py

# 2. INSTALIRAJ PAKETE
echo "[2/8] Instaliram sistem ske pakete..."
sudo apt update
sudo apt install -y \
    python3 python3-venv python3-pip \
    ca-certificates iproute2 iputils-ping \
    procps util-linux kmod udev systemd-sysv \
    mount wget rsync parted dosfstools \
    grub-efi-amd64 grub-efi-amd64-bin grub-efi-amd64-signed efibootmgr \
    lightdm lightdm-gtk-greeter openbox xorg xinit dbus-x11 \
    network-manager pulseaudio thunar xfce4-terminal firefox \
    debootstrap squashfs-tools xorriso isolinux syslinux-efi \
    mtools dos2unix build-essential git

# 3. INSTALIRAJ PYTHON PAKETE
echo "[3/8] Instaliram Python pakete..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyyaml jinja2 flask flask-socketio requests

# 4. KREIRAJ VELES-OS SPECIFIČNI ROOTFS
echo "[4/8] Kreiram VELES rootfs strukturu..."

mkdir -p build/rootfs
mkdir -p build/rootfs/opt/veles
mkdir -p build/rootfs/opt/veles/modules
mkdir -p build/rootfs/opt/veles/web
mkdir -p build/rootfs/opt/veles/core
mkdir -p build/rootfs/opt/veles/system
mkdir -p build/rootfs/etc/veles
mkdir -p build/rootfs/var/lib/veles
mkdir -p build/rootfs/var/log/veles

# 5. KOPIRAJ VELES APLIKACIJU
echo "[5/8] Kopiram VELES aplikaciju u rootfs..."
cp -r core/ build/rootfs/opt/veles/
cp -r desktop/ build/rootfs/opt/veles/
cp -r installer/ build/rootfs/opt/veles/
cp -r services/ build/rootfs/opt/veles/
cp -r system/ build/rootfs/opt/veles/
cp -r scripts/ build/rootfs/opt/veles/
cp main.py build/rootfs/opt/veles/
cp build_image.py build/rootfs/opt/veles/

# 6. KREIRAJ VELES SYSTEMD SERVISE
echo "[6/8] Kreiram systemd servise..."

# Glavni VELES servis
cat > build/rootfs/etc/systemd/system/veles.service << 'EOF'
[Unit]
Description=Veles OS Core Service
After=network.target dbus.service
Wants=network.target

[Service]
Type=simple
User=veles
Group=veles
WorkingDirectory=/opt/veles
ExecStart=/usr/bin/python3 /opt/veles/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=/opt/veles
Environment=VELES_HOME=/opt/veles

[Install]
WantedBy=multi-user.target
EOF

# VELES Dashboard Web servis
cat > build/rootfs/etc/systemd/system/veles-web.service << 'EOF'
[Unit]
Description=Veles Dashboard Web Interface
After=veles.service network.target
Wants=veles.service

[Service]
Type=simple
User=veles
Group=veles
WorkingDirectory=/opt/veles
ExecStart=/usr/bin/python3 -m flask --app desktop/app run --host=0.0.0.0 --port=5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. KREIRAJ VELES KORISNIKA
echo "[7/8] Kreiram VELES korisnika..."
cat > build/rootfs/usr/local/bin/setup-veles-user << 'EOF'
#!/bin/bash
# Setup VELES user
useradd -m -s /bin/bash veles
echo "veles:veles" | chpasswd
usermod -aG sudo,audio,video,netdev,plugdev veles

# VELES home dir
mkdir -p /home/veles/.config/veles
mkdir -p /home/veles/.local/share/veles
chown -R veles:veles /home/veles/.config /home/veles/.local

# Kopiraj VELES config
cp -r /opt/veles/config/* /home/veles/.config/veles/ 2>/dev/null || true
chown -R veles:veles /home/veles/.config/veles

# Auto-start VELES Dashboard
cat > /home/veles/.xsession << 'XSESSION'
#!/bin/bash
exec openbox-session &
sleep 2
python3 /opt/veles/main.py &
sleep 3
firefox http://localhost:5000 &
XSESSION
chmod +x /home/veles/.xsession
chown veles:veles /home/veles/.xsession
EOF
chmod +x build/rootfs/usr/local/bin/setup-veles-user

# 8. KREIRAJ GRUB I BOOT KONFIGURACIJU
echo "[8/8] Kreiram boot konfiguraciju..."

cat > build/rootfs/etc/default/grub << 'EOF'
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="Veles OS"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
EOF

# BILANCIJA - POKRENI BUILD
echo ""
echo "=========================================="
echo "  ✅ SVE SPREMNO ZA BUILD"
echo "=========================================="
echo ""
echo "Pokrećem build_image.py..."
sudo python3 build_image.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  🎉 VELES-OS USPJEŠNO IZGRAĐEN!"
    echo "=========================================="
    echo ""
    echo "ISO fajl: build/iso/veles-os.iso"
    echo ""
    echo "Da testiraš u VM:"
    echo "  qemu-system-x86_64 -cdrom build/iso/veles-os.iso -m 4096 -vga std -soundhw hda"
    echo ""
    echo "Da napraviš USB:"
    echo "  sudo dd if=build/iso/veles-os.iso of=/dev/sdX bs=4M status=progress"
    echo ""
    echo "VELEŠKI POZDRAV! 🚀"
else
    echo ""
    echo "❌ Build neuspješan. Provjeri log: build.log"
fi
