This Metadynamics simulations was performed on alanine dipeptide. To reweight the calculations, we can start by preparing the files with the *prepare_files.sh* scripts, that will create the COLVARS, HEIGHTS and SIGMAS file.

Now if we analyze the pyitre.json file, you will see something like this

```json
{
"stride":10,
"kT":1.0,
"colvars_file":"COLVARS",
"heights_file":"HEIGHTS",
"sigmas_file":"SIGMAS",
"starting_height":2.0,
"iterations":20,
"boundaries":[-3.14,3.14,-3.14,3.14]
}
```
The *plain.py* and *use_nb.py* works exactly as for the *wt_meta* case, with the difference of course that in this case, we declare the boundaries either in the JSON file or in the numba script. 

Now pay attention, because it seems that the first evaluation, done with LESS steps, take more time. This is known for numba, and is expected. As the first compilation of the code is performed, then the jitted function runs faster and the time decreases. I this suggest you to run a mock evaluation (i.e. with 100 steps) and then perform a full calculation that will run faster.
