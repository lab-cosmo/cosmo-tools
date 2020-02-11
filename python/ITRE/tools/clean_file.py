"""
This scripts clean a file from unnecessary field. This is quite useful when
postprocesing a PLUMED 2.0 calculation that uses a file format such as

#! FIELDS time cv1 cv2 etc...
0.0 0.234 0.1466 ....
1.0 0.735 0.5477 ....
2.0 0.460 0.3246 ....

This script is used to  clean the file and save only the cvs, for example:

0.234 0.1466 ....
0.735 0.5477 ....
0.460 0.3246 ....

It requires the file name, which columns are needed, and weather or not steps
need to be discarded.
"""

import numpy as np
import argparse as ap

parser = ap.ArgumentParser(description='A script to clean files so that they are ready to be used in reweight')
parser.add_argument('--file','-f',help='file to clean')
parser.add_argument('--start','-s',help='First column to retain')
parser.add_argument('--end','-r',help='First columns to discards')
parser.add_argument('--columns','-c',type=int,nargs='+',help='list of columns to use')
parser.add_argument('--discard','-d',type=int,help='discard rows before this steps')
parser.add_argument('--keep','-k',type=int,help='keep rows before this steps')
parser.add_argument('--output','-o',help='name of the output file')

args = parser.parse_args()
data = np.loadtxt(args.file)

if args.output:
    file_out = args.output
else:
    file_out = '{}_clean'.format(args.file)

if args.discard:
    top = args.discard
else:
    top = 0

if args.keep:
    bottom = args.keep
else:
    bottom = len(data)


if args.columns:
    np.savetxt(file_out,data[top:bottom,args.columns])
else:
    np.savetxt(file_out,data[top:bottom,args.start:args.end])
