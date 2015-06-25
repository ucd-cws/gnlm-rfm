__author__ = 'Andy'

import arcpy
import config

# Import custom toolbox
arcpy.ImportToolbox(config.sup_tbx)

# reference tools using tool alias _ tbx alias
arcpy.TabulateArea02_sas()

