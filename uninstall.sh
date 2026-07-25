#!/bin/bash
echo "Uninstalling Fedora Voice Agent..."

# Remove Python dependencies (optional, as they were installed with pip --user or venv)
# pip uninstall -r requirements.txt -y

# Remove udev rules
if [ -f /etc/udev/rules.d/80-ydotool.rules ]; then
    echo "Removing udev rules..."
    sudo rm /etc/udev/rules.d/80-ydotool.rules
    sudo udevadm control --reload
fi

# Clean up build artifacts or logs if any
rm -rf __pycache__
rm -rf src/__pycache__

echo "Uninstallation complete. You may verify by checking /etc/udev/rules.d/"
