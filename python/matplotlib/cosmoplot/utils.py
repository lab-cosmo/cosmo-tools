#!/usr/bin/python

import numpy as np
import matplotlib.colors as mplcolors

"""
    RGB for screen/online, CMYK for print
    Matplotlib uses RGB, focus on that for now

    Assumes Matplotlib RGB are sRGB

    References:
    P. Tol, "Colour Schemes", SRON Technical Note,
    Document No. SRON/EPS/TN/09-002, Issue 3.1, 23 September 2018

    G. Sharma, W. Wu, and E. N. Dalal, "The CIEDE2000 Color-Difference
    Formula: Implementation Notes, Supplementary Test Data,
    and Mathematical Observations", 
    Color Research and Applications 30:21-30, 2005

    F. Vienot, H. Brettel, and J. D. Mollon, "Digital Video Colourmaps
    foro Checking the Legibility of Displays by Dichromats",
    Color Research and Application 24:243-252, 1999

    H. Brettel, F. Vienot, J. D. Mollon, "Computerized Simulation of
    Color Appearance for Dichromats", Journal of the Optical Society
    of America A 14:2647-2655, 1997

    CIELAB color space, https://en.wikipedia.org/wiki/CIELAB_color_space

    sRGB, https://en.wikipedia.org/wiki/SRGB
"""

def deuteranomaly(c):
   """
        Simulates green blindness in a color

        ---Arguments---
        c: RGB tuple with values between 0 and 1
    """
    cc = np.zeros(3)
    cc[0] = (4211 + 0.677*(255*c[1])**2.2 + 0.2802*(255*c[0])**2.2)**(1.0/2.2)
    cc[1] = (4211 + 0.677*(255*c[1])**2.2 + 0.2802*(255*c[0])**2.2)**(1.0/2.2)
    cc[2] = (4211 + 0.95724*(255*c[2])**2.2 + 0.02138*(255*c[1])**2.2 \
            - 0.02138*(255*c[0])**2.2)**(1.0/2.2)
    return cc/255

def protanomaly(c):
    """
        Simulates red blindness in a color

        ---Arguments---
        c: RGB tuple with values between 0 and 1
    """
    cc = np.zeros(3)
    cc[0] = (782.7 + 0.8806*(255*cc[1])**2.2 + 0.1115*(255*cc[0])**2.2)**(1.0/2.2)
    cc[1] = (782.7 + 0.8806*(255*cc[1])**2.2 + 0.1115*(255*cc[0])**2.2)**(1.0/2.2)
    cc[2] = (782.7 + 0.992052*(255*cc[2])**2.2 - 0.003974*(255*cc[1])**2.2 \
            + 0.003974*(255*cc[0])**2.2)**(1.0/2.2)
    return cc/255

def XYZtoRGB(XYZ, gamma=True):
    # Assumes D65 illuminant
    tranform = np.array([[3.2406, -1.5372, -0.4986],
                         [-0.9689, 1.8758, 0.0415],
                         [0.0557, -0.2040, 1.0570]])
    RGB = np.einsum('i,j->ij', transform, XYZ)
    if gamma is True:
        a = 0.055
        RGB[np.where(RGB <= 0.0031308)] = 12.92*RGB
        RGB[np.where(RGB > 0.0031308)] = (1 + a)*RGB**(1.0/2.4) - a
    return RGB

def RGBtoXYZ(RGB, gamma=True):
    # Assumes D65 illuminant
    if gamma is True:
        a = 0.055
        RGB[np.where(RGB <= 0.04045)] = RGB/12.92
        RGB[np.where(RGB > 0.04045)] = ((RGB + a)/(1 + a))**2.4
    transform = np.array([[0.4124, 0.3576, 0.1805],
                          [0.2126, 0.7152, 0.0722],
                          [0.0193, 0.1192, 0.9505]])
    XYZ = np.einsum('i,j->ij', transform, RGB)
    return XYZ

def XYZtoLAB(c, illuminant='D65'):
    if illuminant not in ['D65', 'D50']:
        raise ValueError("Invalid illuminant: options are 'D65' \
                (default) or 'D50'")
    def f(t):
        delta = 6.0/29.0
        if t > (delta)**3:
            return t**(1.0/3.0)
        else:
            return t/(3*delta**3) + 4.0/29.0

    if illuminant == 'D65':
        Xn = 95.047
        Yn = 100.0
        Zn = 108.883
    else:
        Xn = 96.6797
        Yn = 100.0
        Zn = 82.5188
    L = 116*f(Y/Yn) - 16
    a = 500*(f(X/Xn) - f(Y/Yn))
    b = 200*(f(Y/Yn) - f(Z/Zn))
    return np.array([L, a, b])

def LABtoXYZ(c):
    if illuminant not in ['D65', 'D50']:
        raise ValueError("Invalid illuminant: options are 'D65' \
                (default) or 'D50'")
    def f(t):
        delta = 6.0/29.0
        if t < delta:
            return t**3
        else:
            return 3*delta**2 * (t - 4.0/29.0)
    if illuminant == 'D65':
        Xn = 95.047
        Yn = 100.0
        Zn = 108.883
    else:
        Xn = 96.6797
        Yn = 100.0
        Zn = 82.5188
    X = Xn*f((L + 16.0)/116.0 + a/500.0)
    Y = Yn*f((L + 16.0)/116.0)
    Z = Zn*f((L + 16.0)/116.0 - b/200.0)
    return np.array([X, Y, Z])

def deltaE(LAB1, LAB2, kl=1.0, kc=1.0, kh=1.0):
    # TODO: modify to take multiple color pairs as input
    # (i.e., LAB1 and LAB2 are M x 3 matrices
    # and the if statements use np.where
    Cstar1 = np.sqrt(LAB1[1]**2 + LAB1[2]**2)
    Cstar2 = np.sqrt(LAB2[1]**2 + LAB2[2]**2)
    Cstar12 = (Cstar1 + Cstar2)/2

    G = 0.5*(1.0 - np.sqrt(Cstar12**7/(Cstar12**7 + 25.0**7)))
    a1 = (1.0 + G)*LAB1[1]
    a2 = (1.0 + G)*LAB2[1]

    C1 = np.sqrt(a1**2 + LAB1[2]**2)
    C2 = np.sqrt(a2**2 + LAB2[2]**2)

    h1 = 0.0
    h2 = 0.0

    if a1 == 0 and LAB1[2] == 0:
        h1 = 0.0
    else:
        h1 = np.rad2deg(np.arctan2(LAB1[2], a1))

    if a2 == 0 and LAB2[2] == 0:
        h2 = 0.0
    else:
        h2 = np.rad2deg(np.arctan2(LAB2[2], a2))

    dL = LAB2[0] - LAB1[0]
    dC = C2 - C1
    dh = 0.0

    if C1*C2 == 0.0:
        dh = 0.0
    elif C1*C2 != 0.0 and np.abs(h2 - h1) <= 180.0:
        dh = h2 - h1
    elif C1*C2 != 0.0 and (h2 - h1) > 180.0:
        dh = (h2 - h1) - 360.0
    elif C1*C2 != 0.0 and (h2 - h1) < -180.0:
        dh = (h2 - h1) + 360.0

    dH = 2.0*np.sqrt(C1*C2)*np.sin(np.deg2rad(deltah/2.0))

    L = (LAB1[0] + LAB2[0])/2.0
    C = (C1 + C2)/2.0

    h = 0.0
    if np.abs(h1 - h2) <= 180.0 and C1*C2 != 0.0:
        h = (h1 + h2)/2.0
    elif np.abs(h1 - h2) > 180.0 and (h1 + h2) < 360.0 and C1*C2 != 0.0:
        h = (h1 + h2 + 360.0)/2.0
    elif np.abs(h1 - h2) > 180.0 and (h1 + h2) >= 360.0 and C1*C2 != 0.0:
        h = (h1 + h2 - 360.0)/2.0
    elif C1*C2 == 0:
        h = h1 + h2

    T = 1.0 - 0.17*np.cos(np.deg2rad(h - 30.0)) \
            + 0.24*np.cos(np.deg2rad(2.0*h)) \
            + 0.32*np.cos(np.deg2rad(3.0*h + 6.0)) \
            - 0.20*np.cos(np.deg2rad(4.0*h - 63.0))

    dTheta = 30.0*np.exp(-((h - 275.0)/25.0)**2)
    Rc = 2.0*np.sqrt(C**7/(C**7 + 25.0**7))
    Sl = 1.0 + (0.015*(L - 50.0)**2)/np.sqrt(20.0 + (L - 50.0)**2)
    Sc = 1.0 + 0.045*C
    Sh = 1.0 + 0.015*C*T
    Rt = -np.sin(np.deg2rad(2.0*theta))*Rc

    dE = np.sqrt((dL/(kl*Sl))**2 + (dC/(kc*Sc))**2 \
            + (dH/(kh*Sh))**2 + Rt*(dC/(kc*Sc))*(dH/(kh*Sh)))
