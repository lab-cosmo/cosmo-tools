This ATLAS simulations was performed on a toy system, with the potential defined in the plumed.dat input. To reweight the calculations, we can start by preparing the files with the *clean_files.sh* scripts, that will create the files required from the ITRE module.

Now if we analyze the pyitre.json file, you will see something like this

```json
{
"stride":1,
"kT":1.0,
"colvars_file":"LOWD_CVS_clean",
"heights_file":"HEIGHTS",
"sigmas_file":"SIGMAS",
"thetas_file":"THETA_clean",
"starting_height":2.0,
"iterations":20
}
```

Differently from the *we_meta* example, here we also define the
1. *thetas_file*: which instruct the ITRE module that the calculation is a ATLAS calculation and those are the switching functions required to calculate the instantaneous bias and c(t)

Now the *plain_plus_nb.py* script contain an implementation with and without numba. As you can see, the directives.json is readed from file and is parsed to the Itre() class. Then the c(t) is calculated, and a comparison between the two is done.

In the *use_nb.py* script, the same c(t) calculation is repeated but with numba and for different length of the data. It also print on the screen the time required in seconds to perform the c(t) calculation with a given number of steps.

Now pay attention, because it seems that the first evaluation, done with LESS steps, take more time. This is known for numba, and is expected. As the first compilation of the code is performed, then the jitted function runs faster and the time decreases. I this suggest you to run a mock evaluation (i.e. with 100 steps) and then perform a full calculation that will run faster.
