#!/bin/bash

set -e 

SERVER="flopp@grus.uberspace.de"
BASE="/home/flopp/projects/unicode"

# setup directories
ssh $SERVER mkdir -p $BASE $BASE/scripts $BASE/www $BASE/www/data $BASE/www/templates

# copy stuff
scp scripts/*            $SERVER:$BASE/scripts/
scp www/*.py             $SERVER:$BASE/www/
scp www/templates/*.html $SERVER:$BASE/www/templates/
scp other/unicode.fcgi   $SERVER:fcgi-bin/
scp other/.htaccess      $SERVER:html/unicode/

ssh $SERVER $BASE/scripts/kill-server.sh
ssh $SERVER $BASE/scripts/get-datafiles.sh $BASE
ssh $SERVER $BASE/scripts/setup-venv.sh    $BASE
