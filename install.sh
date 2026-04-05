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

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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
mkdir -p "$SCRIPT_DIR/$THEME_DIR"

PROCEED=false

read -p "Do you want install $THEME_NAME?  [y/N]: " answer
case "$answer" in
    y|Y) PROCEED=true ;;
    n|N) PROCEED=false ;;
    *) PROCEED=false ;;
esac

if ! $PROCEED; then
    exit 0;
fi

echo "Checking your distrs. . ."

classes=()
names=()

# # while IFS= read -r line; do
# #     classes+=("$(echo "$line" | cut -d' ' -f1)")
# #     names+=("$(echo "$line" | cut -d' ' -f2-)")
# # done < <(grub-mkconfig 2>/dev/null | grep "^menuentry" | while read line; do
# #     name=$(echo "$line" | grep -oP "menuentry '\\K[^']+")
# #     class=$(echo "$line" | grep -oP '(?<=--class )[a-z0-9_-]+' | grep -v 'gnu\|os\|submenu' | head -1)
# #     echo "$class $name"
# # done | awk '!seen[$1]++')
while IFS= read -r line; do
    classes+=("$(echo "$line" | cut -d' ' -f1)")
    names+=("$(echo "$line" | cut -d' ' -f2-)")
done < <(sudo grub-mkconfig 2>/dev/null \
  | grep '^menuentry' \
  | grep -v 'submenu' \
  | while IFS= read -r line; do
      name=$(echo "$line"  | grep -oP "menuentry ['\"]\\K[^'\"]+")
      class=$(echo "$line" | grep -oP '(?<=--class )[a-z0-9_-]+' \
              | grep -v 'linux\|gnu\|os' | head -1)
      echo "$class $name"
  done | awk '!seen[$1]++')

echo "Making virtual env for python. . ."
VENV="$SCRIPT_DIR/assets/.venv"

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$SCRIPT_DIR/assets/requirements.txt"
fi

echo "Render frames"
for i in "${!classes[@]}"; do
    "$VENV/bin/python" "$SCRIPT_DIR/assets/create_images.py" "$i" "${classes[$i]}" "${names[@]}"
done

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
