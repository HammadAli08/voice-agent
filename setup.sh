#!/bin/bash
set -e

# Fedora Voice Agent Setup Script
# Compatible with Fedora Linux 43 (Workstation Edition)

echo "Starting Fedora Voice Agent Setup..."

# 1. Check Fedora Version
if ! grep -q "Fedora" /etc/os-release; then
    echo "Error: This script is intended for Fedora Linux."
    exit 1
fi

# 2. Install System Dependencies
echo "Installing system dependencies..."
sudo dnf install -y \
    python3.11 python3-devel \
    portaudio-devel pipewire-devel \
    ydotool wl-clipboard jq \
    gtk-layer-shell-devel \
    dbus-devel gobject-introspection-devel \
    alsa-lib-devel pulseaudio-libs-devel \
    libcairo-devel pkg-config

# 3. Install Python Dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure ydotool permissions
echo "Configuring ydotool permissions..."
if [ ! -f /etc/udev/rules.d/80-ydotool.rules ]; then
    echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/80-ydotool.rules
    sudo udevadm control --reload
    sudo udevadm trigger
fi

# Ensure user is in input group
if ! groups $USER | grep &>/dev/null 'input'; then
    sudo usermod -aG input $USER
    echo "User added to input group. You may need to relogin for changes to take effect."
fi

# 5. Start ydotool daemon (user service)
echo "Setting up ydotool service..."
# Ideally this should be a systemd user unit, but for now we'll just check if it runs
# A proper systemd unit file will be created in scripts/systemd

echo "Setup complete! Please configure your .env file."
