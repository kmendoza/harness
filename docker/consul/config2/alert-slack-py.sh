#!/bin/bash

export CONSUL_DATA=$(cat)

echo "+++++++++"
echo $CONSUL_DATA
echo "+++++++++"

source /home/consul/.bashrc && python /scripts/alerter.py $CONSUL_DATA

