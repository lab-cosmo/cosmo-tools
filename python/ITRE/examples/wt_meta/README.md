This Metadynamics simulations was performed on a toy system, with the potential defined in the plumed.dat input. To reweight the calculations, we can start by preparing the files with the *prepare_files.sh* scripts, that will create the COLVARS, HEIGHTS and SIGMAS file.

Now if we analyze the pyitre.json file, you will see something like this

```json
{
"stride":10,
"kT":1.0,
"colvars_file":"COLVARS",
"heights_file":"HEIGHTS",
"sigmas_file":"SIGMAS",
"starting_height":2.0,
"iterations":20
}
```

1. Now the *stride* key instruct the code to calculate c(t) that many steps during the calculation.
2. The *kT* is of course the kT in the correct units, i.e. the one that you used in your calculation.
3. We then set the files that are used in the reweighting procedure. What we need are the files that contains the CVS, the heights of the gaussian as a function of time, as well as the width of the gaussian, i.e. the *colvars_file*, *heights_file* and *sigmas_file*. 
4. The *starting_height* is required if you are using an output produced by PLUMED2.0 for example, where in well tempered calculation it is saved on file an estimate of the fes, rather than the gaussian heights. This is thus required to renormalize the heights.
5. *iterations* controls the number of iterations to be done in ITRE

Now the *plain.py* script contain an implementation without numba. As you can see, the directives.json is readed from file and is parsed to the Itre() class. Then the c(t) is calculated, and a comparison is done between the instantaneous bias calculated from Itre and the one written by PLUMED2.0.

In the *use_nb.py* script, the same c(t) calculation is repeated but with numba and for different length of the data. It also print on the screen the time required in seconds to perform the c(t) calculation with a given number of steps.

Now pay attention, because it seems that the first evaluation, done with LESS steps, take more time. This is known for numba, and is expected. As the first compilation of the code is performed, then the jitted function runs faster and the time decreases. I this suggest you to run a mock evaluation (i.e. with 100 steps) and then perform a full calculation that will run faster.



