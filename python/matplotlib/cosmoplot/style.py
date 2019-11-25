#!/usr/bin/python

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from . import colorbars

one_col = (3.54, 3.54)
two_col = (7.08, 3.54)
one_col_poster =  (7.08, 7.08)
two_col_poster = (14.16, 7.08)

color_cycle = ['#000000', '#aa0000', '#000080', '#008000', '#800080', '#808080', 
        '#ffcc00', '#d45500', '#c83771', '#c0c0c0']
marker_cycle = ['o', 's', '^', 'v', '<', '>', '+', 'x']
linestyle_cycle = ['-', '--', ':', '-.']
hatch_cycle = ['/', '//', '\\', '\\\\', 'x', 'xx']
fill_cycle = ['full', 'none', 'bottom', 'left', 'top', 'right']

def set_style(styleType='article'):

    # Set general COSMO style
    substyles = ['article', 'presentation', 'poster']
    if styleType not in substyles:
        raise ValueError("Invalid substyle: options are 'article', \
                'presentation', or 'poster'")
    else:
        if styleType == 'presentation' or styleType == 'poster':
            plt.style.use('cosmoLarge')
        else:
            plt.style.use('cosmo')

    # Make colorbars
    colorbars.cbarHot()
    colorbars.cbarBWR()
    colorbars.cbarPhi()

