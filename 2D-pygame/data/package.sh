#!/bin/sh
#rm -f cards.zip
zip -u -R cards.zip cards/cardsets cards/*/checklist.txt cards/*/oracle.txt cards -i cards\*.jpg cards/*/obj/*
