import numpy as np
import os
import numba as nb
from .metadynamics import Metadynamics
from .atlas import Atlas
from .utils import printitre

class Itre(object):
    """ This class implement the Iterative Trajectory Reweighing method,
    as presented in

    Giberti, F., Cheng, B., Tribello, G. A., & Ceriotti, M. (2019).
    Iterative unbiasing of quasi-equilibrium sampling.
    Journal of chemical theory and computation.

    To use this class in a script or a notebook, it is necessary to either
    pass a json directive containing the information on what calculation should
    be performed, or alternatively to pass the relevant required information
    directly to the class after it has been instantiated.
    Please visit the example folder in the module root directory to understand
    how to use it.
    """
    def __init__(self):
        super(Itre, self).__init__()
        self.__required_properties_list = ['colvars_file','heights_file' \
                                          ,'sigmas_file']
        self.__optional_properties = ['kT','stride','thetas_file','iterations',\
                                      'starting_height','wall_file']

        for el in self.__required_properties_list:
            object.__setattr__(self,'{}'.format(el),None)

        for el in self.__optional_properties:
            object.__setattr__(self,'{}'.format(el),None)

        self.__setattr__('stride',10)
        self.__setattr__('kT',1.0)
        self.__setattr__('beta',1.0)
        self.__setattr__('iterations',20)
        self.__setattr__('starting_height',1.0)
        self.__setattr__('has_matrix',False)
        self.__setattr__('has_thetas',False)
        self.__setattr__('use_numba',False)

    def print_dict(self):
        """
        Print a mock dictionary containing the directives that the class accept
        with a description of what each directive activates or signifies.
        """

        dd={
        'colvars_file':'a file containing the collective variables directly \
                        used to construct the potential',
        'heights_file':'a file containing the heights of the hill as a function \
                        of time',
        'sigmas_file':'the sigma or covariance used in the Gaussian functions \
                       to reposit the repulsive bias',
        'kT':'kT in the right units',
        'stride':' the stride used to evaluate the bias matrix (hence c(t)). \
                   This is useful to avoid calculating c(t) at every step',
        'thetas_file':' for a ATLAS calculations, the activation functions of \
                        all the basins.',
        'iterations':'How many self consistent iterations to do.',
        'starting_height':'The original height of the Gaussian used in the \
                           calculation',
        'wall_file': 'a file containing the potential from restraint acting \
                      on the simulation.',
        'has_thetas':'for an ATLAS calculation set True if we set thetas \
                      directly, not from a json object',
        'use_numba':'wether to use numba or not.'
        }

        printitre(json.dumps(dd, indent=4, sort_keys=True))


    def from_dict(self,dict):
        """
        Read the directive from a json object (dictionary) and populate the
        attributes of the class.

        Parameters
        ----------
        dict : a dictionary containing the optional and required directives
               to use the class.
        """
        for key in dict.keys():
            if key in self.__required_properties_list or \
               key in self.__optional_properties:
                self.__setattr__('{}'.format(key),dict[key])
                printitre("Found {} directive with {} value".format(key, \
                                                                    dict[key]))

        if os.path.isfile(self.colvars_file):
            colvars = np.loadtxt(self.colvars_file)
        if os.path.isfile(self.sigmas_file):
            sigmas = np.loadtxt(self.sigmas_file)
            if len(colvars)!=len(sigmas):
                raise ValueError('Length of colvars and sigmas is different!')
        if os.path.isfile(self.heights_file):
            heights = np.loadtxt(self.heights_file)
            if len(colvars)!=len(heights):
                raise ValueError('Length of colvars and heights is different!')
            heights /=heights[0]
            heights *= self.starting_height

        if self.thetas_file is not None:
            if os.path.isfile(self.thetas_file):
                thetas = np.loadtxt(self.thetas_file)
                if len(colvars)!=len(thetas):
                    raise ValueError('Length of colvars and thetas is different!')
                self.__setattr__('has_thetas',True)

        if self.wall_file is not None:
            if os.path.isfile(self.wall_file):
                wall = np.loadtxt(self.wall_file)
                if len(colvars)!=len(wall):
                    raise ValueError('Length of colvars and wall is different!')
        else:
            wall = np.zeros(len(colvars))

        self.__setattr__('colvars',colvars)
        self.__setattr__('wall',wall)
        self.__setattr__('sigmas',sigmas)
        self.__setattr__('heights',heights)
        self.__setattr__('beta',self.kT)

        if self.has_thetas:
            self.__setattr__('thetas',thetas)

        self.__setattr__('steps',len(self.colvars))
        self.__setattr__('n_evals',int(self.steps//self.stride))

    def calculate_bias_matrix(self):
        """
        This function is a selector. Depending on which directives has
        been set, it selects if the simulations that we are reweighting is a
        Metadynamics, a Atlas or other calculations. It also check if the
        calculation should be performed with or withouth numba.

        The class call classes that evaluate the lagged and instantaneous bias.

        Returns
        -------
        bias_matrix : a n_eval,n_eval float matrix containing the
                      lagged potential. The instantaneous potential is
                      equal to the diagonal of this matrix
        """
        if self.has_thetas:
            printitre(" You are reweighing an ATLAS calculations ")
            bias_scheme = Atlas()
            if self.use_numba:
                printitre("With numba enabled.")
                matrix = bias_scheme.calculate_bias_matrix_nb(self.colvars,
                                                              self.sigmas,
                                                              self.heights,
                                                              self.wall,
                                                              self.thetas,
                                                              self.n_evals,
                                                              self.stride,
                                                        len(self.colvars[0]))
            else:
                printitre("With numba disabled")
                matrix = bias_scheme.calculate_bias_matrix(self.colvars,
                                                           self.sigmas,
                                                           self.heights,
                                                           self.wall,
                                                           self.thetas,
                                                           self.n_evals,
                                                           self.stride)
        else:
            printitre(" You are reweighing a METAD calculations ")
            bias_scheme = Metadynamics()
            if self.use_numba:
                printitre("With numba enabled.")
                matrix = bias_scheme.calculate_bias_matrix_nb(self.colvars,
                                                              self.sigmas,
                                                              self.heights,
                                                              self.wall,
                                                              self.n_evals,
                                                              self.stride,
                                                        len(self.colvars[0]))
            else:
                printitre("With numba disabled")
                matrix = bias_scheme.calculate_bias_matrix(self.colvars,
                                                           self.sigmas,
                                                           self.heights,
                                                           self.wall,
                                                           self.n_evals,
                                                           self.stride)
        self.has_matrix=True
        printitre("")
        return matrix

    def calculate_c_t(self):
        """
        Calculate c(t) by solving the self consistent equation n 13 presented
        in the publication.

        If the bias matrix has not been calculate, calculate the matrix and
        then proceed in the self consistent cycle.
        """
        if not self.has_matrix:
            printitre("The lagged potential matrix was not calculated")
            printitre("Calculating it now!")
            printitre("")
            self.bias_matrix=self.calculate_bias_matrix()
            self.instantaneous_bias = np.diag(self.bias_matrix)

        iter = 0
        self.ct = np.zeros((self.iterations,self.n_evals))
        matw = np.tril(np.exp(-self.bias_matrix*self.beta))
        for iteration in range(1,self.iterations):
            printitre(" Done iteration n {}".format(iteration))
            offset = self.instantaneous_bias-self.ct[iteration-1]
            vec1 = np.exp(offset*self.beta)
            res = matw.dot(vec1)
            norm = np.cumsum(vec1)
            self.ct[iteration] = -self.kT*np.log(res/norm)

        printitre("Finished, c(t) calculated!")
        printitre("")


if __name__ == '__main__':
    printitre("A __main__ implementation is still missing")
    printitre("please implement it or use it as a module.")
