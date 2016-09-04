#!/bin/bash

set -e 

SERVER="flopp@grus.uberspace.de"
BASE="/home/flopp/projects/unicode"

echo "-- setting up directory structure"
ssh $SERVER mkdir -p $BASE $BASE/scripts $BASE/www $BASE/www/data $BASE/www/static $BASE/www/static/css $BASE/www/static/img $BASE/www/templates

echo "-- copying files"
scp config.py            $SERVER:$BASE/
scp scripts/*            $SERVER:$BASE/scripts/
scp www/*.py             $SERVER:$BASE/www/
scp www/static/css/*     $SERVER:$BASE/www/static/css/
scp www/static/img/*     $SERVER:$BASE/www/static/img/
scp www/templates/*.html $SERVER:$BASE/www/templates/
scp other/unicode.fcgi   $SERVER:fcgi-bin/
scp other/.htaccess      $SERVER:html/unicode/

echo "-- running post copy script"
ssh $SERVER $BASE/scripts/post-copy.sh $BASE

echo "-- done"
