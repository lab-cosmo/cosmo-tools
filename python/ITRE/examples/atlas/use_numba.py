import sys
sys.path.append('../../')
import itre
import json
import os
import matplotlib.pyplot as plt
import numpy as np
import time


i_bias = np.loadtxt('bias',skiprows=2,usecols=1)
stride=10
colvars=np.loadtxt('LOWD_CVS_clean')
sigmas=np.loadtxt('SIGMAS')
heights=np.loadtxt('HEIGHTS')
thetas=np.loadtxt('THETA_clean')
plumed_ct=np.loadtxt('c_t_{}'.format(stride))

times=[]
end = len(colvars)
for ss in range(2,end+3,end):
   new_it=itre.Itre()
   new_it.kT=1.0
   new_it.use_numba=True
   new_it.colvars=colvars[:ss]
   new_it.wall = np.zeros(ss)
   new_it.sigmas=sigmas[:ss]
   new_it.thetas=thetas[:ss]
   new_it.has_thetas=True
   new_it.heights=heights[:ss]
   new_it.stride=stride
   new_it.n_evals=int(ss/new_it.stride)
   new_it.calculate_c_t()
   plt.plot(new_it.instantaneous_bias)
   plt.plot(i_bias[:ss:new_it.stride],'--',alpha=0.5)
   plt.plot(plumed_ct)
   plt.plot(new_it.ct[-1].T)
   plt.show()
