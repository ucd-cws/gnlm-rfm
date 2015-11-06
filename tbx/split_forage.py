__author__ = 'Andy'

#  split forage into two group (manure and non-manure)

import os
import arcpy
import config

#get folder
wdir = config.gnlmrfm

# location of caml 1990 raster
caml1990 = os.path.join(wdir, r"data\caml\1990", "landuse.tif")

print(caml1990)

search_dist = 1609.34  # in meters = 1 mile

# create a sub raster with just CAFO landuse classes (1902, 1903, or 1904)

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "landuse.tif"
arcpy.MakeRasterLayer_management(in_raster="landuse.tif", out_rasterlayer="MakeRas_test2tif1", where_clause=""""Value" IN (1902, 1903, 1904)""", envelope="-223350 -344650 129000 298550", band_index="")

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "MakeRas_test2tif1"
arcpy.gp.EucDistance_sa("MakeRas_test2tif1", "C:/Users/Andy/Documents/ArcGIS/Default.gdb/EucDist_afr1", "", "50", "")


# build new raster using con statement????
