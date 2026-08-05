#!/bin/sh
# Legacy login helper invoked by menu.c's build script.
dialog --title "Login" --password=hunter2secret --menu "Choose an option:" 20 60 4
