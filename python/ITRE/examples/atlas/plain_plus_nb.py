import sys
sys.path.append('../../')
import itre
import json
import os
import matplotlib.pyplot as plt
import numpy as np
import time

if os.path.isfile("pyitre.json"):
    with open("pyitre.json",'r') as json_file:
        directives = json.load(json_file)


i_bias = np.loadtxt('bias',skiprows=2,usecols=1)
it = itre.Itre()
it.from_dict(directives)
it.use_numba=False

plumed_ct=np.loadtxt('c_t_{}'.format(it.stride))


start=time.time()
it.calculate_c_t()
end=time.time()
raw_time=end-start
ref_ct = it.ct[-1].T
plt.plot(it.instantaneous_bias)
plt.plot(i_bias[::it.stride],'--')
plt.plot(ref_ct,'o')
plt.plot(plumed_ct,'.')
plt.show()

print("bias matrix:{}".format(it.bias_matrix[30,30]))

colvars=np.loadtxt('LOWD_CVS_clean')
sigmas=np.loadtxt('SIGMAS')
heights=np.loadtxt('HEIGHTS')
thetas=np.loadtxt('THETA_clean')

times=[]
list_ss = [31,1000]
for ss in list_ss:
    print(ss)
    new_it=itre.Itre()
    new_it.use_numba=True
    new_it.colvars=colvars[:ss]
    new_it.wall = np.zeros(ss)
    new_it.sigmas=sigmas[:ss]
    new_it.thetas=thetas[:ss]
    new_it.has_thetas=True
    new_it.heights=heights[:ss]
    new_it.kT=1.0
    new_it.stride=int(1)
    new_it.n_evals=int(ss/new_it.stride)
    start = time.time()
    new_it.calculate_c_t()
    end = time.time()
    plt.plot(new_it.instantaneous_bias)
    plt.plot(i_bias[::new_it.stride])
    plt.show()
    plt.plot(new_it.ct[-1].T)
    plt.plot(ref_ct,'-.')
    plt.plot(plumed_ct,'--',alpha=0.5)
    plt.show()
    plt.matshow(new_it.bias_matrix)
    plt.show()
    times.append(end-start)
    print("bias matrix:{}".format(new_it.bias_matrix[30,30]))

