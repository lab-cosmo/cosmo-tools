# ITRE: Iterative Trajectory Reweight

This python modules contains an implementation of the ITRE algorithm presented in _Giberti, F., Cheng, B., Tribello, G. A., & Ceriotti, M._ (2019). _Iterative unbiasing of quasi-equilibrium sampling._ **Journal of chemical theory and computation.**

The current implementation scales as T*(T-1), with T the number of evaluation required to calculate c(t). All the methods have an implementation in plain python, as well as an implementation in numba (which is required).

We suggest to use the module with a *virtual environment*, and install all the packages directly from the *requirements.txt* via *pip*.

To understand how to use the class, I suggest to check the examples contained in the *examples* folder.
