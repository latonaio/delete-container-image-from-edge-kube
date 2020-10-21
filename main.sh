#!/bin/sh

python3 -u main.py
# /bin/sh -c "sleep 3"
/bin/sh -c "sleep 10000"
curl -s -X POST localhost:10001/quitquitquit
