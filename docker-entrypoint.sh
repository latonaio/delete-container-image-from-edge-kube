#!/bin/sh

python3 -u main.py
/bin/sh -c "sleep 3"
curl -s -X POST localhost:10001/quitquitquit
