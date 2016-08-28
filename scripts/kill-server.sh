#!/bin/bash

set -e 

ps aux | grep unicode.fcgi | grep -v grep | awk '{ print $2; }' | while read P ; do
    echo "killing: $P"
    kill $P
done
