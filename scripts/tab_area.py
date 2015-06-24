__author__ = 'Andy'

import arcpy
import os

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")


def tabulate_area_w_overlaps(data, idfield, raster, raster_value, out_tables, cell_size):
	"""tabulate raster area with overlapping polygons"""

	# loop through each of the features in the in zone feature
	cursor = arcpy.SearchCursor(data)  # loops through using a cursor

	for row in cursor:
		try:
			fid = row.getValue(idfield)

			sql_builder = """{0} = {1}""".format(arcpy.AddFieldDelimiters(data, idfield), fid)

			arcpy.MakeFeatureLayer_management(data, "featlayer", sql_builder)

			print("working on: {0}".format(fid))

			out_table_temp = os.path.join(out_tables, "tab_area_" + str(fid))

			print("temp table: {0}".format(out_table_temp))

			#  TabulateArea (in_zone_data, zone_field, in_class_data, class_field, out_table, {processing_cell_size})
			arcpy.sa.TabulateArea("featlayer", idfield, raster, raster_value, out_table_temp, cell_size)

			arcpy.Delete_management("featlayer")

		except Exception as e:
			print e.message



def merge_tables():
	pass




def polys2rasters(input_polgyons, idfield, output_folder, cell_size):
	"""converts polygons to seperate rasters in the same folder or gdb using unique ID. Folder is faster"""
	cursor = arcpy.SearchCursor(input_polgyons)
	for row in cursor:
		try:
			fid = row.getValue(idfield)

			sql_builder = """{0} = {1}""".format(arcpy.AddFieldDelimiters(input_polgyons, idfield), fid)

			arcpy.Delete_management("featlayer")
			arcpy.MakeFeatureLayer_management(input_polgyons, "featlayer", sql_builder)

			print("Converting ID#: {0} to a raster".format(fid))

			out_raster = os.path.join(output_folder, "well_" + str(fid))

			# convert to raster
			arcpy.FeatureToRaster_conversion("featlayer", idfield, out_raster, cell_size)
			arcpy.Delete_management("featlayer")

		except Exception as e:
			errorLog = r'C:\Users\Andy\Documents\gnlm-rfm\log.txt'
			print e.message
			try:
				with open(errorLog,'a') as errorMsg:
					errorMsg.write("%s,%s\n" % (fid, e.message))
			except RuntimeError:
				arcpy.AddMessage("Unable to log")
				arcpy.AddMessage(RuntimeError.message)


def merge_tables(folder, output):
	pass


def get_list_of_rasters(folder):
	pass


def raster_tab_area(raster, output):
	pass

def raster_zonal_stats(raster, output):
	pass


polys2rasters(r"C:\Users\Andy\Documents\gnlm-rfm\results\Wells.gdb\Vector\wells_Buffer", "OBJECTID",
              r"C:\Users\Andy\Documents\gnlm-rfm\results\buf  fers.gdb", "50")