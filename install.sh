#!/bin/bash
# ===============================================================
# Boykisser GRUB Theme Installer
# Repository: https://github.com/VixurHD/BoykisseGrub
# ===============================================================

set -e

THEME_NAME="Boykisser"
THEME_DIR="/boot/grub/themes"
RECOVERY_DIR="/boot/grub/recoveryfiles"
HAVE_OS_PROBER=false
GRUB_CFG="/etc/default/grub"
GRUB_FILE="/boot/grub/grub.cfg"
CAN_RECOVERY=false

TASK_RECOVERY=false
TASK_INSTALL=false

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)."
    exit 1
fi
# Check If the script is in the right directory
if [ ! -d "$THEME_NAME" ]; then
    echo "The $THEME_NAME theme folder was not found next to the script."
    exit 1
fi

echo '
++----------------------------------------------------------------------------------------++
++----------------------------------------------------------------------------------------++
|| /$$$$$$$                      /$$       /$$                                            ||
||| $$__  $$                    | $$      |__/                                            ||
||| $$  \ $$  /$$$$$$  /$$   /$$| $$   /$$ /$$  /$$$$$$$ /$$$$$$$  /$$$$$$   /$$$$$$      ||
||| $$$$$$$  /$$__  $$| $$  | $$| $$  /$$/| $$ /$$_____//$$_____/ /$$__  $$ /$$__  $$     ||
||| $$__  $$| $$  \ $$| $$  | $$| $$$$$$/ | $$|  $$$$$$|  $$$$$$ | $$$$$$$$| $$  \__/     ||
||| $$  \ $$| $$  | $$| $$  | $$| $$_  $$ | $$ \____  $$\____  $$| $$_____/| $$           ||
||| $$$$$$$/|  $$$$$$/|  $$$$$$$| $$ \  $$| $$ /$$$$$$$//$$$$$$$/|  $$$$$$$| $$           ||
|||_______/  \______/  \____  $$|__/  \__/|__/|_______/|_______/  \_______/|__/           ||
||                     /$$  | $$                                                          ||
||                    |  $$$$$$/                                                          ||
||                     \______/                                                           ||
||                          /$$$$$$  /$$$$$$$  /$$   /$$ /$$$$$$$           /$$  /$$$$$$  ||
||                         /$$__  $$| $$__  $$| $$  | $$| $$__  $$         /$$/ /$$__  $$ ||
||                        | $$  \__/| $$  \ $$| $$  | $$| $$  \ $$        /$$/ |__/  \ $$ ||
||                        | $$ /$$$$| $$$$$$$/| $$  | $$| $$$$$$$        /$$/     /$$$$$/ ||
||                        | $$|_  $$| $$__  $$| $$  | $$| $$__  $$      |  $$    |___  $$ ||
||                        | $$  \ $$| $$  \ $$| $$  | $$| $$  \ $$       \  $$  /$$  \ $$ ||
||                        |  $$$$$$/| $$  | $$|  $$$$$$/| $$$$$$$/        \  $$|  $$$$$$/ ||
||                         \______/ |__/  |__/ \______/ |_______/          \__/ \______/  ||
||                                                                                        ||
++----------------------------------------------------------------------------------------++
++----------------------------------------------------------------------------------------++
'

# Ensure theme directory exists
echo "Checking for theme directory..."
mkdir -p "$THEME_DIR"

# Checking recovery dir and check recovery files
echo "Checking for recovery directory..."
if [ -d "$RECOVERY_DIR" ]; then
    if [ -f "$RECOVERY_DIR/10_linux" ]; then
        CAN_RECOVERY=true
    fi
else
    mkdir -p "$RECOVERY_DIR"
fi

if $CAN_RECOVERY; then
    echo "We can restore grub to its previous state"
    while true; do
    read -p "Are we want restore grub? [y/n]: " answer
        case "$answer" in
            y|Y) TASK_RECOVERY=true; break ;;
            n|N) TASK_RECOVERY=false; break ;;
            *) echo "Please enter y or n" ;;
        esac
    done
fi

if ! $TASK_RECOVERY; then
    while true; do
    read -p "Do you want install $THEME_NAME? [y/n]: " answer
        case "$answer" in
            y|Y) TASK_INSTALL=true; break ;;
            n|N) TASK_INSTALL=false; break ;;
            *) echo "Please enter y or n" ;;
        esac
    done
fi

echo "Planned actions:"
if $TASK_RECOVERY; then
    echo "Recovery your grub on saved position"
elif $TASK_INSTALL; then
    echo "Install grub theme on your system"
fi

PROCEED=false

read -p "Continue? [y/N]: " answer
case "$answer" in
    y|Y) PROCEED=true; break ;;
    n|N) PROCEED=false; break ;;
    *) PROCEED=false ;;
esac

if ! $PROCEED; then
    exit 0;
fi
# Copy theme files
echo "Installing theme..."
cp -r "$THEME_NAME" "$THEME_DIR/" || {
    echo "Failed to copy theme files."
    exit 1
}

# Configure GRUB to use the new theme
echo "Updating GRUB configuration..."
if grep -q '^GRUB_THEME=' "$GRUB_CFG"; then
    sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"${THEME_DIR}/${THEME_NAME}/theme.txt\"|" "$GRUB_CFG"
else
    echo "" >> "$GRUB_CFG"
    echo "GRUB_THEME=\"${THEME_DIR}/${THEME_NAME}/theme.txt\"" >> "$GRUB_CFG"
fi

# Regenerate GRUB
echo "Rebuilding GRUB configuration..."
if command -v grub-mkconfig >/dev/null 2>&1; then
    grub-mkconfig -o "$GRUB_FILE" >/dev/null
    echo "GRUB configuration updated successfully."
else
    echo "grub-mkconfig not found. Please update your GRUB manually."
    exit 1
fi

echo ""
echo "Installation complete!"
echo "Reboot to see your new Boykisser GRUB theme."
echo ""
