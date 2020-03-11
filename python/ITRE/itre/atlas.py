import numpy as np
import numba as nb

class Atlas(object):
    """This class implement the calculation of the bias matrix for an ATLAS
       calculation."""
    def __init__(self):
        super(Atlas, self).__init__()

    def kernel(self,a,b,c):
        """This function evaluate the gaussian between two points given the
           covariance

           Parameters
           ----------
           a : first point (either a float or a array of float)
           b : second point (either a float or a array of float)
           c : covariance (either a float or a array of float)

           Returns
           -------
           the value of the Gaussian overlap
        """
        dist = (a-b)/c
        dist = 0.5 * dist.dot(dist)
        return np.exp(-dist)

    def calculate_bias_matrix(self,colvars,sigmas,heights,wall,thetas,n_evals,stride):
        """
        Evaluate the bias matrix by looping over time. A recursive formula is
        used so that the evaluation scale as T*(T-1) where T is the number of
        evaluation required from the ITRE class.

        Parameters
        ----------
        colvars : the values of the collective variables
        sigmas : the covariances use to evaluate the overlap kernel
        heights : the heights of the hills deposited in the simulations
        wall : the values of the restraint acting in the simulation
        thetas : the values of the activation function theta for ATLAS
        n_evals :  the number of evaluation to do (T in here)
        stride : the stride between two different evaluation.

        Returns
        -------
        bias_matrix : a T*T float matrix containing the lagged potential matrix
        """
        n_minima = len(thetas[0])
        dims = int(len(colvars[0])//n_minima)
        bias_matrix = np.zeros((n_evals,n_evals))

        for i in range(n_evals):
            upper_index = int(i*stride)
            sum_bias = 0.0
            for k in range(upper_index+1):
                for minimum in range(n_minima):
                    start = int(minimum*dims) ; end = int(minimum*dims+dims)
                    switch = thetas[upper_index,minimum]*thetas[k,minimum]
                    sum_bias += self.kernel(colvars[upper_index,start:end],colvars[k,start:end],sigmas[k,start:end])*heights[k]*switch

            bias_matrix[i,i] = sum_bias

        for i in range(n_evals):
            ref_index= int(i*stride)
            for j in range(i,n_evals-1):
                lower_index = int(j*stride)
                upper_index = int((j+1)*stride)
                sum_bias = 0.0
                for t in range(lower_index,upper_index):
                    for minimum in range(n_minima):
                        start = int(minimum*dims) ; end = int(minimum*dims)+dims
                        switch = thetas[ref_index,minimum]*thetas[t,minimum]
                        sum_bias += self.kernel(colvars[ref_index,start:end],colvars[t,start:end],sigmas[t,start:end])*heights[t]*switch

                bias_matrix[j+1,i] = bias_matrix[j,i] + sum_bias

        for i in range(n_evals):
            upper_index = int(i*stride)
            for j in range(i,n_evals):
                bias_matrix[j,i] += wall[upper_index]
                
        return bias_matrix

    @staticmethod
    @nb.jit
    def calculate_bias_matrix_nb(colvars,sigmas,heights,wall,thetas,n_evals,stride,dims):
        n_minima = len(thetas[0])
        dims = int(len(colvars[0])//n_minima)
        bias_matrix = np.zeros((n_evals,n_evals))
        dist = np.zeros(dims)

        for i in range(n_evals):
            upper_index = int(i*stride)
            sum_bias = 0.0
            for k in range(upper_index+1):
                for minimum in range(n_minima):
                    start = int(minimum*dims) ; end = int(minimum*dims+dims)
                    switch = thetas[upper_index,minimum]*thetas[k,minimum]
                    dist = (colvars[upper_index,start:end]-colvars[k,start:end])/sigmas[k,start:end]
                    dist2 = 0.5 * dist.dot(dist)
                    sum_bias += np.exp(-dist2)*heights[k]*switch

            bias_matrix[i,i] = sum_bias

        for i in range(n_evals):
            ref_index= int(i*stride)
            for j in range(i,n_evals-1):
                lower_index = int(j*stride)
                upper_index = int((j+1)*stride)
                sum_bias = 0.0
                for t in range(lower_index,upper_index):
                    for minimum in range(n_minima):
                        start = int(minimum*dims) ; end = int(minimum*dims)+dims
                        switch = thetas[ref_index,minimum]*thetas[t,minimum]
                        dist = (colvars[ref_index,start:end]-colvars[t,start:end])/sigmas[t,start:end]
                        dist2 = 0.5 * dist.dot(dist)
                        sum_bias += np.exp(-dist2)*heights[t]*switch

                bias_matrix[j+1,i] = bias_matrix[j,i] + sum_bias


        for i in range(n_evals):
            upper_index = int(i*stride)
            for j in range(i,n_evals):
                bias_matrix[j,i] += wall[upper_index]

        return bias_matrix
