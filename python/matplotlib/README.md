Matplotlib COSMO Style
======================

style.py
--------
**Author**  
Benjamin Helfrecht

**Description**  
Contains custom colobar definitions,
color, linestyle, marker, and hatch cycles,
and other utilities for defining and customizing style

**Usage**  
1.  Ensure that `style.py` is in your $PYTHONPATH
    and that cosmo.mplstyle and cosmoLarge.mplstyle
    is in the directory containing
    your Matplotlib styles (often /home/user/.config/matplotlib/stylelib).
2.  To set the COSMO style, `import cosmoplot.style as cosmostyle`
    and call `cosmostyle.set_style(styleType)`, where `styleType`
    is 'article', 'presentation', or 'poster'.
    The appropriate font and figure sizes will be set
    and the colorbars will be registered in Matplotlib.
3.  Colorbars can be called from `cbar = plt.get_cmap(name)`,
    where 'name' is 'cbarHot' (sequential), 'cbarBWR' (diverging),
    or 'cbarPhi' (periodic).

colorbars.py
------------
**Author**  
Benjamin Helfrecht

**Description**  
Contains the definitions for the COSMO
custom colorbars

**Usage**  
Import the colorbars with:
`import cosmoplot.colorbars as cosmocbars`

cosmo.mplstyle
--------------
**Author**  
Benjamin Helfrecht

**Description**  
Matplotlib style file with custom plot setup
for articles

**Usage**  
The COSMO style is set automatically when calling 
`cosmo.set_style()` or `cosmo.set_style(article)`,
but can also be set with `plt.style.use('cosmo')`.

cosmoLarge.mplstyle
-------------------
**Author**  
Benjamin Helfrecht

**Description**  
Matplotlib style file with custom plot setup
for presentations and posters

**Usage**  
The COSMO Large style is set automatically when calling 
`cosmo.set_style(presentation)` or `cosmo.set_style(poster)`,
but can also be set with `plt.style.use('cosmoLarge')`.

