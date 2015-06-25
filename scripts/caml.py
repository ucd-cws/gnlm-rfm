# tabulates areas within polygons for caml landuse rasters

import arcpy
import config
import os

# Import custom toolbox
arcpy.ImportToolbox(config.sup_tbx)

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")


sub2 = r"C:\Users\Andy\Documents\gnlm-rfm\results\Wells.gdb\Vector\wells_Buffer_sub2"
output = r"C:\Users\Andy\Documents\gnlm-rfm\results\results.gdb"

in_zone_data = sub2
zone_field = "WELLID"

# overwrite output must be set to true in order to get all of the overlapping polygons processed.
arcpy.env.overwriteOutput = "True"

years = [1945, 1960, 1975, 1990, 2005]

for year in years:
	print "Processing CAML: %s" %year
	caml_path = os.path.join(config.gnlmrfm, "data\caml", str(year), "landuse.tif")
	table_name = "CAML_" + str(year) + "_sub3"

	# snap raster to caml input
	arcpy.env.snapRaster = caml_path

	# reference tools using tool alias _ tbx alias
	arcpy.TabulateArea02_sas(in_zone_data, zone_field, caml_path, "Value", os.path.join(output, table_name), "50")
