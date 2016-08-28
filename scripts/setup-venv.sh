#!/bin/bash

set -e

TARGET_DIR="$1/venv/"

if [ ! -d "$1" ] ; then
    echo "Base dir doesn't exist: $1"
    exit 1
fi

if [ -d "$TARGET_DIR" ] ; then
    exit 0
fi

echo "setting up venv: $TARGET_DIR"

~/bin/virtualenv -p python3 "$TARGET_DIR"

source "$TARGET_DIR/bin/activate"
pip3 install flash
pip3 install flipflop
