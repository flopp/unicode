#!/bin/bash

cd $1
cp ./other/.htaccess ~/html/unicode/
cp ./other/unicode.fcgi ~/fcgi-bin/
./scripts/kill-server.sh
./scripts/get-datafiles.sh $1
./scripts/setup-venv.sh    $1

