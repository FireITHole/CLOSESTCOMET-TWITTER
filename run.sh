#!/bin/bash

token=`cat token.txt`
git pull -a "https://$token@github.com/FireITHole/CLOSESTCOMET-TWITTER.git"
python3 NASA-TWITTER.py
git add *
CURRENTDATE=`date +"%Y-%m-%d/%T"`
git commit -a -m "POST ${CURRENTDATE}"
git push -u "https://$token@github.com/FireITHole/CLOSESTCOMET-TWITTER.git"
