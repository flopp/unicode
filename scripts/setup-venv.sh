#!/bin/bash

set -e

TARGET_DIR="$1/venv/"

if [ ! -d "$1" ] ; then
    echo "Base dir doesn't exist: $1"
    exit 1
fi

if [ ! -d "$TARGET_DIR" ] ; then
    echo "setting up venv: $TARGET_DIR"
    
    for VE_BIN in /usr/bin/virtualenv ~/bin/virtualenv ; do
        if [ -e $VE_BIN ] ; then
            $VE_BIN -p python3.7 "$TARGET_DIR"
            break
        fi
    done
fi

source "$TARGET_DIR/bin/activate"
pip3 install flask
pip3 install flipflop
pip3 install Flask-Caching
pip3 install wikipedia
