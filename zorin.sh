#!/usr/bin/env bash

echo "███████╗ ██████╗ ██████╗ ██╗███╗   ██╗     ██████╗ ███████╗    ██████╗ ██████╗  ██████╗ "
echo "╚══███╔╝██╔═══██╗██╔══██╗██║████╗  ██║    ██╔═══██╗██╔════╝    ██╔══██╗██╔══██╗██╔═══██╗"
echo "  ███╔╝ ██║   ██║██████╔╝██║██╔██╗ ██║    ██║   ██║███████╗    ██████╔╝██████╔╝██║   ██║"
echo " ███╔╝  ██║   ██║██╔══██╗██║██║╚██╗██║    ██║   ██║╚════██║    ██╔═══╝ ██╔══██╗██║   ██║"
echo "███████╗╚██████╔╝██║  ██║██║██║ ╚████║    ╚██████╔╝███████║    ██║     ██║  ██║╚██████╔╝"
echo "╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ "
echo "|ZORIN-OS-PRO| |Script v5.0.0| |Overhauled By NamelessNanasi/CortezJEL| |original by PEAKYCOMMAND|"
echo ""
echo "(Please note this version ONLY works on Zorin 17 and 16)"
echo ""
echo "(to use this script on Zorin 16 add the -6 flag or -7 for zorin 17)"
echo ""
echo "THIS CODE AND ACCOMPANYING DOCUMENTATION WERE OVERHAULED SIGNIFICANTLY BY NamelessNanashi/CortezJEL, "
echo "IF YOU GOT THIS CODE ELSEWHERE KNOW THAT THE CODE SHOULD NOT BE FULLY TRUSTED DUE TO THE IMPROPER ETIQUETTE AND ACTIONS OF THE ORIGINAL DEV!"
echo ""
echo "THIS CODE AND ACCOMPANYING DOCUMENTATION WERE OVERHAULED SIGNIFICANTLY BY NamelessNanashi/CortezJEL, "
echo "IF YOU GOT THIS CODE ELSEWHERE KNOW THAT THE CODE SHOULD NOT BE FULLY TRUSTED DUE TO THE IMPROPER ETIQUETTE AND ACTIONS OF THE ORIGINAL DEV!"
sleep 10

# Prompt user
echo "Please Enter your sudo password!"

# Sudo echo so it always propts here
sudo echo > /dev/null

# Parse command line arguments for flag
OPTION_COUNT=0
while getopts "67M" opt; do
  case $opt in
    6)
        version="16"
    ;;
    7)
        sixteen="17"
    ;;
    M)
        more="true"
    ;;
    esac
done
if [ "$OPTION_COUNT" -gt 1 ]; then echo "too many options"; fi

echo ""
echo "Preparing to install dependencies..."
echo ""

# Install ca-certificates
sudo apt-get install ca-certificates aptitude

sleep 2

echo ""
echo "Updating the defaut sources.list for Zorin's custom resources..."
echo ""

if [ "$version" = "16" ]; then   
            # Copy zorin16.list mod
            sudo \cp -f ./zorin16.list /etc/apt/sources.list.d/zorin.list

elif [ "$version" = "17" ]; then
            # Copy zorin17.list mod
            sudo \cp -f ./zorin17.list /etc/apt/sources.list.d/zorin.list
            # Add the required apt-key to be safe
else
            echo ""
            echo "You are not running this script correctly, read the GitHub https://github.com/CortezJEL/Zorin-OS-Pro/ for more info"
            echo ""
            exit 1
fi

sleep 2

echo ""
echo "Adding Zorin's Package Keys..."
echo ""

sudo \cp -n ./zorin_apt-cdrom.gpg /etc/apt/trusted.gpg.d/
sudo \cp -n ./zorin-os-premium.gpg /etc/apt/trusted.gpg.d/
sudo \cp -n ./zorin-os.gpg /etc/apt/trusted.gpg.d/

sleep 2

echo ""
echo "adding premium flags..."
echo ""

# introduces premium user agent
sudo \cp -f ./99zorin-os-premium-user-agent /etc/apt/apt.conf.d/

sleep 2

echo ""
echo "Adding premium content..."
echo ""

# update packages
sudo aptitude update ; sudo apt-get update

if [ "$version" = "16" ]; then   
            # install 16 pro content
            sudo aptitude install zorin-additional-drivers-checker zorin-appearance zorin-appearance-layouts-shell-core zorin-appearance-layouts-shell-premium zorin-appearance-layouts-support zorin-auto-theme zorin-connect zorin-desktop-session zorin-desktop-themes zorin-exec-guard zorin-exec-guard-app-db zorin-gnome-tour-autostart zorin-icon-themes zorin-os-artwork zorin-os-default-settings zorin-os-docs zorin-os-file-templates zorin-os-keyring zorin-os-minimal zorin-os-overlay zorin-os-premium-keyring zorin-os-printer-test-page zorin-os-pro zorin-os-pro-creative-suite zorin-os-pro-productivity-apps zorin-os-pro-wallpapers zorin-os-pro-wallpapers-16 zorin-os-restricted-addons zorin-os-standard zorin-os-tour-video zorin-os-upgrader zorin-os-wallpapers zorin-os-wallpapers-16 zorin-os-www-browser zorin-sound-theme zorin-windows-app-support-installation-shortcut
elif [ "$version" = "17" ]; then
            # install 17 pro content
            sudo aptitude install zorin-additional-drivers-checker zorin-appearance zorin-appearance-layouts-shell-core zorin-appearance-layouts-shell-premium zorin-appearance-layouts-support zorin-auto-theme zorin-connect zorin-desktop-session zorin-desktop-themes zorin-exec-guard zorin-exec-guard-app-db zorin-gnome-tour-autostart zorin-icon-themes zorin-os-artwork zorin-os-default-settings zorin-os-docs zorin-os-file-templates zorin-os-keyring zorin-os-minimal zorin-os-overlay zorin-os-premium-keyring zorin-os-printer-test-page zorin-os-pro zorin-os-pro-creative-suite zorin-os-pro-productivity-apps zorin-os-pro-wallpapers zorin-os-pro-wallpapers-16 zorin-os-pro-wallpapers-17 zorin-os-restricted-addons zorin-os-standard zorin-os-tour-video zorin-os-upgrader zorin-os-wallpapers zorin-os-wallpapers-16 zorin-os-wallpapers-17 zorin-os-www-browser zorin-sound-theme zorin-windows-app-support-installation-shortcut
else
            echo ""
            echo "You are not running this script correctly, read the GitHub https://github.com/CortezJEL/Zorin-OS-Pro/ for more info"
            echo ""
            exit 1
fi
echo ""
echo ""
echo "All done!"
echo ""
echo 'Please Reboot your Zorin Instance... you can do so with "sudo reboot"'
echo ""
echo ""
