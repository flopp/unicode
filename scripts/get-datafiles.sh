#!/bin/bash

set -e

TARGET_DIR="$1/www/data/"
NAMESLIST_TARGET="$TARGET_DIR/NamesList.txt"
BLOCKS_TARGET="$TARGET_DIR/Blocks.txt"
NAMESLIST_URL="ftp://www.unicode.org/Public/9.0.0/ucd/NamesList.txt"
BLOCKS_URL="ftp://www.unicode.org/Public/9.0.0/ucd/Blocks.txt"

if [ ! -d "$TARGET_DIR" ] ; then
    echo "TARGET_DIR does not exist: $TARGET_DIR"
    exit 1
fi

if [ ! -f "$NAMESLIST_TARGET" ] ; then
    echo "fetching NamesList.txt"
    wget -O "$NAMESLIST_TARGET" "$NAMESLIST_URL"
fi

if [ ! -f "$BLOCKS_TARGET" ] ; then
    echo "fetching Blocks.txt"
    wget -O "$BLOCKS_TARGET" "$BLOCKS_URL"
fi

