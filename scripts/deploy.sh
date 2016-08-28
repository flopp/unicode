#!/bin/bash

set -e 

SERVER="flopp@grus.uberspace.de"
BASE="/home/flopp/projects/unicode"

echo "-- setting up directory structure"
ssh $SERVER mkdir -p $BASE $BASE/scripts $BASE/www $BASE/www/data $BASE/www/templates

echo "-- copying files"
scp -v config.py            $SERVER:$BASE/
scp -v scripts/*            $SERVER:$BASE/scripts/
scp -v www/*.py             $SERVER:$BASE/www/
scp -v www/templates/*.html $SERVER:$BASE/www/templates/
scp -v other/unicode.fcgi   $SERVER:fcgi-bin/
scp -v other/.htaccess      $SERVER:html/unicode/

echo "-- running kill script"
ssh $SERVER $BASE/scripts/kill-server.sh

echo "-- updating data files"
ssh $SERVER $BASE/scripts/get-datafiles.sh $BASE

echo "-- setting up venv"
ssh $SERVER $BASE/scripts/setup-venv.sh    $BASE
