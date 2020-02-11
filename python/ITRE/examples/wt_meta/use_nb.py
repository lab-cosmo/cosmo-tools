import sys
sys.path.append('../../')
import itre
import json
import os
import matplotlib.pyplot as plt
import numpy as np
import time

colvars=np.loadtxt('COLVARS')
sigmas=np.loadtxt('SIGMAS')
heights=np.loadtxt('HEIGHTS')

iters=1
times = []
for ss in range(1000,len(colvars),100):

    new_it=itre.Itre()
    new_it.use_numba=True
    new_it.colvars=colvars[:ss]

    new_it.wall=np.zeros(len(colvars[:ss]))
    new_it.sigmas=sigmas[:ss]
    new_it.heights=heights[:ss]/heights[0]*2.0
    new_it.stride=10
    new_it.n_evals=int(ss/10)
    start = time.time()
    new_it.calculate_c_t()
    end = time.time()
    print("{} steps processed in {} s".format(ss,end-start))
    times.append([ss,end-start])
    plt.plot(new_it.ct[-1].T)
    iters = iters + 1 

plt.show()

print()
print("Scaling summary:")
for k in times:
    print("{} steps performed in {} seconds".format(k[0],k[1]))



