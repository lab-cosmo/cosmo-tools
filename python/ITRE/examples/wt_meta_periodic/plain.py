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


i_bias = np.loadtxt('bias',usecols=1,skiprows=2)

it = itre.Itre()
it.kT=300
it.from_dict(directives)

start=time.time()

it.calculate_c_t()

end=time.time()
raw_time=end-start
print("execution completed in {}".format(raw_time))

ref_ct = it.ct[-1].T

plt.plot(it.instantaneous_bias,label="V(s,t) itre")
plt.plot(i_bias[::it.stride],label="V(s,t)")
plt.plot(ref_ct,label="c(t)")
plt.legend()
plt.show()


np.savetxt('c_t.dat',ref_ct)
