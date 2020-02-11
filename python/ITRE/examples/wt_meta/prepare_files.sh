#!/bin/bash

python ../../tools/clean_file.py -f HILLS -c 1 2 -o COLVARS 
python ../../tools/clean_file.py -f HILLS -c 3 4 -o SIGMAS 
python ../../tools/clean_file.py -f HILLS -c 5 -o HEIGHTS 
