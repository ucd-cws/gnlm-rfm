# ---------------------------------------------------------------------------------------------------
# Name: gnlm-rfm.pyt
# Purpose: ArcGIS python toolbox containing geoprocessing tools for the gnlm rfm project
# Author: Andy Bell (ambell@ucdavis.edu)
# Created: 6/25/2015
# ---------------------------------------------------------------------------------------------------

import arcpy
import os
import config
import caml_area_reclass  # funcs for caml_reclass tool
import math


# add message if a feature class does not has a field in the reserved list of fieldnames
# check fieldnames for reserved names
def check_fieldnames(fc, matchlist):
	"""Checks if a field(s) exist in feature class. Matches should be added as list"""
	fieldList = arcpy.ListFields(fc)
	check = False
	for field in fieldList:
		if field.name in matchlist:
			check = True
			return check
	return check

# drop all non-required fields from table. Will modify existing table so make a copy first!!!
def drop_unnecessary_fields(table):
	# drop fields
	# use ListFields to get a list of field objects
	fieldObjList = arcpy.ListFields(table)

	# create empty list to be populated with field names
	fieldNameList = []

	# for field in object list add the field to the name list. If it is required exclude it.
	for field in fieldObjList:
		if not field.required:
			if field.name == config.well_id_field:
				print "ID field required"
			else:
				fieldNameList.append(field.name)

	# execute delete field to delete all fields in the field list
	if len(fieldNameList) > 0:
		arcpy.DeleteField_management(table, fieldNameList)


class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "Tools for GNLM RFM"
		self.alias = "Tools for groundwater wells"

		# List of tool classes associated with this toolbox
		self.tools = [WellBuffers, caml, caml_reclass, atmo_n, septics, gw_depth, bioclim, cvhm, dist2river, gnlmarea, dirappnload]


class WellBuffers(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Buffer"
		self.description = "Converts each point to a buffered polygon"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_pts = arcpy.Parameter(displayName="Input Well Features", name="well_pts", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_pts.filter.list = ["Point"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DEWorkspace",
								  parameterType="Required", direction="Input")  # TODO force datatype to geodatabase?

		params = [well_pts, results]
		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		# update message to check if the geodatabase is actually empty
		if parameters[1].value:
			output_loc = parameters[1].valueAsText
			msg_exists = "Set output as an empty geodatabase. Either points or buffers already exist"

			if arcpy.Exists(os.path.join(output_loc, "points.shp")):
				parameters[1].setErrormessage(msg_exists)
			elif arcpy.Exists(os.path.join(output_loc, "buffers.shp")):
				parameters[1].setErrormessage(msg_exists)
			elif arcpy.Exists(os.path.join(output_loc, "points")):
				parameters[1].setErrormessage(msg_exists)
			elif arcpy.Exists(os.path.join(output_loc, "buffers")):
				parameters[1].setErrormessage(msg_exists)

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters
		# Parameters
		points = parameters[0]
		out = parameters[1]

		well_points = points.valueAsText
		output = out.valueAsText

		arcpy.AddMessage("Points: %s" % well_points)
		arcpy.AddMessage("Output: %s" % output)

		# Creates copy of the original points
		arcpy.FeatureClassToFeatureClass_conversion(well_points, output, "points")

		try:
			pts = os.path.join(output, "points")

			# create buffer around points (1.5 miles) and save to results
			arcpy.AddMessage("Creating buffers")
			arcpy.Buffer_analysis(pts, os.path.join(output, "buffers"), config.buffer_dist)  # radius hard coded in config
		except:
			pts = os.path.join(output, "points.shp")
			# create buffer around points (1.5 miles) and save to results
			arcpy.Buffer_analysis(pts, os.path.join(output, "buffers"), config.buffer_dist)  # radius hard coded in config

		return

class caml(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Tabulate CAML area"
		self.description = "Tabulate area within buffers from CAML landuse"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DEWorkspace",
								  parameterType="Required", direction="Input")

		years = arcpy.Parameter(displayName="Years", name="years", datatype="GPString", parameterType="Required",
		                        multiValue="True", direction="Input")

		years.filter.list = ["1945", "1960", "1975", "1990", "2005"]

		params = [well_buffers, results, years]
		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters
		in_zone_data = parameters[0].valueAsText
		output = parameters[1].valueAsText
		zone_field = config.well_id_field

		year_string = parameters[2].valueAsText

		years = year_string.split(";")

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = True

		for year in years:
			arcpy.AddMessage("Processing CAML: %s" %year)
			caml_path = os.path.join(config.gnlmrfm, "data\caml", str(year), "landuse.tif")
			table_name = "CAML_" + str(year)

			# snap raster to caml input
			arcpy.env.snapRaster = caml_path

			# reference tools using tool alias _ tbx alias
			arcpy.TabulateArea02_sas(in_zone_data, zone_field, caml_path, "Value", os.path.join(output, table_name), "50")

		return

class caml_reclass(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Reclass CAML area from CSV"
		self.description = "Tabulate area from CAML landuse using csv file with reclass mappings"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		csv_file = arcpy.Parameter(displayName="Reclass Table", name="csv_file", datatype="DEFile",
								  parameterType="Required", direction="Input")

		landuse_area = arcpy.Parameter(displayName="CAML landuse area table", name="landuse_area", datatype="DETable",
								  parameterType="Required", direction="Input")

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [landuse_area, csv_file, results]
		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" %config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters
		# Parameters
		caml_area_table = parameters[0].valueAsText
		reclass_csv = parameters[1].valueAsText
		out = parameters[2].valueAsText

		arcpy.AddMessage(caml_area_table)
		arcpy.AddMessage(reclass_csv)
		arcpy.AddMessage(out)

		base, file = os.path.split(out)
		arcpy.AddMessage(base)
		arcpy.AddMessage("Saving reclassified area as: %s" %file)

		caml_area_reclass.main(caml_area_table, reclass_csv, base, file)

		return

class atmo_n(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Atmospheric Nitrogen Deposition"
		self.description = "Calculate the average N deposition within the well buffers"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well Buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		ndep = arcpy.Parameter(displayName="N Deposition raster", name="ndep", datatype="DERasterDataset",
								 parameterType="Required")

		ndep.value = config.ndep_raster

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [well_buffers, ndep, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		in_zone_data = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_value_raster = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		arcpy.AddMessage("Processing")

		# snap raster to input
		arcpy.env.snapRaster = input_value_raster

		# reference tools using tool alias _ tbx alias
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table,
		                                   statistics_type="ALL", ignore_nodata="DATA")

		return

class septics(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Num. People on Septics Systems"
		self.description = "Calculate the number of people on septic systems within the well buffers"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well Buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		septics = arcpy.Parameter(displayName="Septics raster", name="septics", datatype="DERasterDataset",
								 parameterType="Required")

		septics.value = config.septic_raster

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [well_buffers, septics, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		in_zone_data = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_value_raster = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		arcpy.AddMessage("Processing")

		# snap raster to input
		arcpy.env.snapRaster = input_value_raster

		# reference tools using tool alias _ tbx alias
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table,
		                                   statistics_type="SUM", ignore_nodata="DATA")

		return

class gw_depth(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Groundwater Depth"
		self.description = "Calculate the average groundwater depth within the well buffers"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well Buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		dwr_depth = arcpy.Parameter(displayName="Groundwater depth raster", name="dwr_depth", datatype="DERasterDataset",
								 parameterType="Required")

		dwr_depth.value = config.dwr_depth_raster

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [well_buffers, dwr_depth, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		in_zone_data = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_value_raster = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		arcpy.AddMessage("Processing")

		# snap raster to input
		arcpy.env.snapRaster = input_value_raster

		# reference tools using tool alias _ tbx alias
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table,
		                                   statistics_type="ALL", ignore_nodata="DATA")

		return

class bioclim(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Add Bioclim Data"
		self.description = "Calculate the precipitation data for the wells"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		wells = arcpy.Parameter(displayName="Input Wells", name="wells", datatype="GPFeatureLayer",
		                        parameterType="Required")

		wells.filter.list = ["Point"]

		bioclim = arcpy.Parameter(displayName="Bioclim raster", name="bioclim", datatype="DERasterDataset",
								 parameterType="Required")

		bioclim.value = config.bioclim_raster

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [wells, bioclim, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		input_pts = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_value_raster = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# make temporary feature layer
		temp_file = "TEMP"
		arcpy.MakeFeatureLayer_management(input_pts, temp_file)

		# drop fields
		drop_unnecessary_fields(temp_file)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		arcpy.AddMessage("Processing")
		arcpy.sa.ExtractMultiValuesToPoints(temp_file, input_value_raster)

		# export to table
		arcpy.CopyRows_management(temp_file, output_table)

		# remove temporary point file
		arcpy.Delete_management(temp_file)

		return

class cvhm(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Add CVHM Data"
		self.description = "Calculate the soil texture data for the well buffer"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		wells = arcpy.Parameter(displayName="Input Wells", name="wells", datatype="GPFeatureLayer",
		                        parameterType="Required")

		wells.filter.list = ["Point"]

		cvhm_pts = arcpy.Parameter(displayName="CVHM texture centroids", name="cvhm_pts", datatype="DERasterDataset",
								 parameterType="Required")

		cvhm_pts.value = config.cvhm_centroid_pts

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [wells, cvhm_pts, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		input_pts = parameters[0].valueAsText
		centroids = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# add all input fields to field mappings
		field_map = arcpy.FieldMappings()
		field_map.addTable(input_pts)
		field_map.addTable(centroids)

		# field to keep for centroids (top 8 layers only)
		depths = ["PC_D25", "PC_D75", "PC_D125", "PC_D175", "PC_D225", "PC_D275", "PC_D325", "PC_D375"]

		# set merge rule to mean for centroids
		for depth in depths:
			ind = field_map.findFieldMapIndex(depth)
			arcpy.AddMessage(ind)
			new_fm = field_map.getFieldMap(ind)
			new_fm.mergeRule = 'Mean'
			field_map.replaceFieldMap(ind, new_fm)

		base, file = os.path.split(output_table)
		temp = file + "_temp"
		temp_file = os.path.join(base, temp)

		arcpy.AddMessage("Processing")

		# buffer and cell size must both be in the same units
		dist, unit = config.buffer_dist.split()
		search_radius = float(dist) + math.sqrt(0.5)  # cell size of cvhm raster 1 mile
		search = str(search_radius) + " " + unit

		# spatial join: join centroids info to input_pts (all centroids of grid that intersect (change if buffer is different size)
		arcpy.SpatialJoin_analysis(target_features=input_pts, join_features=centroids, out_feature_class=temp_file,
		                           join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping=field_map,
		                           match_option="WITHIN_A_DISTANCE", search_radius=search, distance_field_name="#")


		# drop all non-required fields from table. Will modify existing table so make a copy first!!!
		# drop fields
		# use ListFields to get a list of field objects
		fieldObjList = arcpy.ListFields(temp_file)

		# create empty list to be populated with field names
		fieldNameList = []

		# for field in object list add the field to the name list. If it is required exclude it.
		for field in fieldObjList:
			if not field.required:
				if field.name == config.well_id_field:
					print "ID field required"
				elif field.name in depths:
					print "Depth Field"
				else:
					fieldNameList.append(field.name)

		# execute delete field to delete all fields in the field list
		if len(fieldNameList) > 0:
			arcpy.DeleteField_management(temp_file, fieldNameList)

		# export to table
		arcpy.CopyRows_management(temp_file, output_table)

		# remove temporary point file
		arcpy.Delete_management(temp_file)

		return

class dist2river(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Distance to Major River"
		self.description = "Calculate the distance to a major river (Mod. Strahler Stream > 3)"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		wells = arcpy.Parameter(displayName="Input Wells", name="wells", datatype="GPFeatureLayer",
		                        parameterType="Required")

		wells.filter.list = ["Point"]

		rivers = arcpy.Parameter(displayName="Major River Flowlines", name="rivers", datatype="GPFeatureLayer",
								 parameterType="Required")

		rivers.value = config.major_river

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [wells, rivers, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		input_pts = parameters[0].valueAsText
		rivers = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# make temporary feature layer
		temp_file = "TEMP"
		arcpy.MakeFeatureLayer_management(input_pts, temp_file)

		# drop fields not needed
		drop_unnecessary_fields(temp_file)

		# find nearest feature
		arcpy.Near_analysis(temp_file, rivers)

		# export to table
		arcpy.CopyRows_management(temp_file, output_table)

		# remove temporary point file
		arcpy.Delete_management(temp_file)

		return

class gnlmarea(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "GNLM area"
		self.description = "Tabulate area within buffers from GNLM major classes"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		reclass_gnlm = arcpy.Parameter(displayName="GNLM reclass raster", name="reclass_gnlm", datatype="DERasterDataset",
								 parameterType="Required")

		params = [well_buffers, results, reclass_gnlm]
		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters
		in_zone_data = parameters[0].valueAsText
		output = parameters[1].valueAsText
		gnlm_reclass = parameters[2].valueAsText
		zone_field = config.well_id_field


		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = True

		# reference tools using tool alias _ tbx alias
		arcpy.TabulateArea02_sas(in_zone_data, zone_field, gnlm_reclass, "Value", output, "50")

		return


class dirappnload(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "N load GNLM variables"
		self.description = "Calculate the loading from GNLM dirapp rasters"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well Buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		raster = arcpy.Parameter(displayName="raster", name="raster", datatype="DERasterDataset",
								 parameterType="Required")

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		params = [well_buffers, raster, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		in_zone_data = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_value_raster = parameters[1].valueAsText
		output_table = parameters[2].valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		arcpy.AddMessage("Processing")

		# snap raster to input
		arcpy.env.snapRaster = input_value_raster

		# reference tools using tool alias _ tbx alias
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table,
		                                   statistics_type="SUM", ignore_nodata="DATA")


class surgo(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "SURGO soils"
		self.description = "Calculate the average organic soil matter and ksat within the well buffers plus the" \
		                   " proportion of area in the hydrologic group and drainage class"

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well Buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		som = arcpy.Parameter(displayName="Organic Soil Matter raster", name="som", datatype="DERasterDataset",
								 parameterType="Required")

		som.value = config.som_raster

		ksat = arcpy.Parameter(displayName="MEAN KSAT raster", name="ksat", datatype="DERasterDataset",
								 parameterType="Required")

		ksat.value = config.ksat_raster

		hydgrp = arcpy.Parameter(displayName="Hydrologic Group raster", name="hydgrp", datatype="DERasterDataset",
								 parameterType="Required")

		hydgrp.value = config.hydgrp_raster

		drain = arcpy.Parameter(displayName="Drainage Class raster", name="drain", datatype="DERasterDataset",
								 parameterType="Required")

		drain.value = config.drain_raster

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DEWorkspace",
								  parameterType="Required", direction="Output")

		params = [well_buffers, som, ksat, hydgrp, drain, results]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		in_zone_data = parameters[0].valueAsText
		zone_field = config.well_id_field # avoids hard coding well id field
		input_som = parameters[1].valueAsText
		input_ksat = parameters[2].valueAsText
		input_hydgrp = parameters[3].valueAsText
		input_drain = parameters[4].valueAsText
		output_location = parameters[5].valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		arcpy.AddMessage("Processing")

		# snap raster to input
		arcpy.env.snapRaster = input_som

		# reference tools using tool alias _ tbx alias
		# SOM
		arcpy.AddMessage("Working on SURGO Soil organic matter....")

		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_som, os.path.join(output_location, "SURGO_SOM"),
		                                   statistics_type="ALL", ignore_nodata="DATA")
		# KSAT
		arcpy.AddMessage("Working on SURGO KSAT....")

		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_ksat, os.path.join(output_location, "SURGO_KSAT"),
		                                   statistics_type="ALL", ignore_nodata="DATA")

		# hydro groups
		arcpy.AddMessage("Working on SURGO hydro groups....")
		arcpy.TabulateArea02_sas(in_zone_data, zone_field, input_hydgrp, "Value",
		                         os.path.join(output_location, "SURGO_HYDROGROUP"), "1000")

		# drain groups
		arcpy.AddMessage("Working on SURGO Draingage....")
		arcpy.TabulateArea02_sas(in_zone_data, zone_field, input_drain, "Value",
		                         os.path.join(output_location, "SURGO_DRAIN"), "1000")

		return
