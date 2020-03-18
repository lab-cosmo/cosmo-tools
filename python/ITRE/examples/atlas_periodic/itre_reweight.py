import numpy as np 
import sys
sys.path.append('../../')
import itre

stride=20
data = np.loadtxt('LOWD_CVS')
colvars = data[1:,1:-1]
heights = data[1:,-1]
sigmas = np.ones(colvars.shape)*0.1

th = np.loadtxt('THETA')
thetas = th[1:,1:-1]
wall = np.zeros(len(colvars))

limit = 100

dumb_it=itre.Itre()
dumb_it.use_numba=True
dumb_it.kT=300
dumb_it.colvars=colvars[:limit]
dumb_it.set_boundaries(np.array([-np.pi,np.pi]*8))
dumb_it.wall = wall
dumb_it.sigmas=sigmas[:limit]
dumb_it.thetas=thetas[:limit]
dumb_it.has_thetas=True
dumb_it.heights=heights[:limit]
dumb_it.stride=stride
dumb_it.n_evals=int(limit/dumb_it.stride)
dumb_it.calculate_c_t()


new_it=itre.Itre()
new_it.kT=300
new_it.use_numba=True
new_it.colvars=colvars
new_it.set_boundaries(np.array([-np.pi,np.pi]*8))
new_it.wall = wall
new_it.sigmas=sigmas
new_it.thetas=thetas
new_it.has_thetas=True
new_it.heights=heights
new_it.stride=stride
new_it.n_evals=int(len(colvars)/new_it.stride)
new_it.calculate_c_t()

np.savetxt('c_t.dat',new_it.ct[-1].T)
np.savetxt('instantaneous_bias.dat',new_it.instantaneous_bias)

