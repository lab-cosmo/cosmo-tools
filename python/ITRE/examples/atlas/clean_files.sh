#!/bin/bash

python ../../tools/clean_file.py -f LOWD_CVS -c 1 2 3 -d 1
python ../../tools/clean_file.py -f THETA -c 1 2 3 -d 1
python ../../tools/clean_file.py -f LOWD_CVS -c 4 -o HEIGHTS -d 1
grep -v \# HEIGHTS | awk '{print 0.1,0.1,0.1}' > SIGMAS


