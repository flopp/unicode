#!/bin/bash

cd $1
./scripts/kill-server.sh
./scripts/get-datafiles.sh $1
./scripts/setup-venv.sh    $1
