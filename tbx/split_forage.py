#  split forage into two group (manure and non-manure)

import os
import arcpy
import config
from arcpy.sa import *

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# get folder
wdir = config.gnlmrfm

# location of caml 1990 raster
caml1990 = os.path.join(wdir, r"data\caml\1990", "landuse.tif")

# location to save file
output_name = os.path.join(wdir, "data\caml\1990", "landuse_manure.tif")

# what is the search distance
search_dist = 1609.34  # in meters = 1 mile

# create a sub raster with just CAFO landuse classes (1902, 1903, or 1904)
#cafo_subset = Con(Raster(caml1990), 1, 0, "Value In (1902, 1903, 1904)")
arcpy.MakeRasterLayer_management(in_raster=caml1990, out_rasterlayer="cafo_subset", where_clause=""""Value" IN (1902, 1903, 1904)""")


# euclidean distance from the CAFO subset
euc_dist = arcpy.sa.EucDistance("cafo_subset", "", "50", "")

# create a sub raster with just manure classes (606, 607, 608, 700, 701, 702, 703)
#arcpy.MakeRasterLayer_management(in_raster=caml1990, out_rasterlayer="manure_subset", where_clause=""""Value" IN (606, 607, 608, 700, 701, 702, 703)""")
manure_subset = Con(Raster(caml1990), Raster(caml1990), 0, "Value In (606, 607, 608, 700, 701, 702, 703)")

# build new raster using con statement????
output_ras = Con(manure_subset > 0, Con(euc_dist < search_dist, Raster(caml1990) + 2000, Raster(caml1990)), Raster(caml1990))

# save raster
output_ras.save(os.path.join(wdir, output_name))

# delete in-memory rasters
try:
	arcpy.Delete_management(manure_subset)
	arcpy.Delete_management(euc_dist)
	arcpy.Delete_management("cafo_subset")

except:
	print("Can't delete temp rasters....")
