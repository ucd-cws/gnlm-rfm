# ---------------------------------------------------------------------------------------------------
# Name: gnlm-rfm.pyt
# Purpose: ArcGIS python toolbox containing geoprocessing tools for the gnlm rfm project
# Author: Andy Bell (ambell@ucdavis.edu)
# Created: 6/25/2015
# ---------------------------------------------------------------------------------------------------

import arcpy
import os
import config
import caml_area_reclass # funcs for caml_reclass tool



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


class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "Tools for GNLM RFM"
		self.alias = "Tools for groundwater wells"

		# List of tool classes associated with this toolbox
		self.tools = [WellBuffers, caml, caml_reclass, atmo_n, septics, gw_depth, bioclim, cvhm, join, dist2river]


class WellBuffers(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Well Buffer"
		self.description = "Converts each point to a buffered polygon"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_pts = arcpy.Parameter(displayName="Input Well Features", name="well_pts", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_pts.filter.list = ["Point"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DEWorkspace",
								  parameterType="Required", direction="Input")

		params = [well_pts, results]
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
		# Parameters
		points = parameters[0]
		out = parameters[1]

		well_points = points.valueAsText
		output = out.valueAsText

		arcpy.AddMessage("Points: %s" %well_points)
		arcpy.AddMessage("Output: %s" %output)

		# Creates copy of the original points
		arcpy.FeatureClassToFeatureClass_conversion(well_points, output, "points")

		pts = os.path.join(output, "points")

		# create buffer around points (1.5 miles) and save to results
		#Buffer_analysis (in_features, out_feature_class, buffer_distance_or_field, {line_side}, {line_end_type}, {dissolve_option}, {dissolve_field})
		arcpy.AddMessage("Creating buffers")
		arcpy.Buffer_analysis(pts, os.path.join(output, "buffers"), "1.5 Miles")  # buffer radius hard coded

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
		#zone_field = "OBJECTID"

		year_string = parameters[2].valueAsText

		years = year_string.split(";")

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = True

		#  TODO: script fails when run on full dataset, runs successfully for a single year than errors out.
		#  Might have something to do with the number of polys (test with 1k successful)

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
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table, statistics_type="ALL", ignore_nodata="DATA")

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
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table, statistics_type="SUM", ignore_nodata="DATA")

		return

class gw_depth(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Groundwater depth"
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
		arcpy.ZonalStatisticsAsTable02_sas(in_zone_data, zone_field, input_value_raster, output_table, statistics_type="ALL", ignore_nodata="DATA")

		return

class bioclim(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Add bioclim data for well"
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

		base, file = os.path.split(input_pts)
		temp = file + "_temp"
		temp_file = os.path.join(base, temp)

		# create copy of the input points since ExtractMultiValues overwrites inputs
		arcpy.AddMessage("Creating temp file: %s" %temp)
		arcpy.FeatureClassToFeatureClass_conversion(input_pts, base, temp)

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
				else:
					fieldNameList.append(field.name)

		# execute delete field to delete all fields in the field list
		arcpy.DeleteField_management(temp_file, fieldNameList)

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
		self.label = "Add CVHM data for well"
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

		# spatial join: join centroids info to input_pts (all centroids of grid that intersect (change if buffer is different size)
		# TODO: make search radius function of buffer size (simple buffer + sqrt(0.5)
		arcpy.SpatialJoin_analysis(target_features=input_pts, join_features=centroids, out_feature_class=temp_file,
		                           join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping=field_map,
		                           match_option="WITHIN_A_DISTANCE", search_radius="2.2071 Miles", distance_field_name="#")

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
		arcpy.DeleteField_management(temp_file, fieldNameList)

		# export to table
		arcpy.CopyRows_management(temp_file, output_table)

		# remove temporary point file
		arcpy.Delete_management(temp_file)

		return

class join(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Join Tables"
		self.description = "Join tables using %s" %config.well_id_field

	def getParameterInfo(self):
		"""Define parameter definitions"""

		wells = arcpy.Parameter(displayName="Input Wells", name="wells", datatype="GPFeatureLayer",
		                        parameterType="Required")

		wells.filter.list = ["Point"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DETable",
								  parameterType="Required", direction="Output")

		ndep = arcpy.Parameter(displayName="NDEP table", name="ndep", datatype="DETable",
								  parameterType="Required", direction="Input")

		bioclim = arcpy.Parameter(displayName="Bioclim table", name="bioclim", datatype="DETable",
								  parameterType="Required", direction="Input")

		gwdepth = arcpy.Parameter(displayName="GW Depth table", name="gwdepth", datatype="DETable",
								  parameterType="Required", direction="Input")

		septics = arcpy.Parameter(displayName="Septics table", name="septics", datatype="DETable",
								  parameterType="Required", direction="Input")

		cvhm = arcpy.Parameter(displayName="CVHM soil table", name="cvhm", datatype="DETable",
								  parameterType="Required", direction="Input")

		lu = arcpy.Parameter(displayName="Landuse reclass table", name="lu", datatype="DETable",
								  parameterType="Required", direction="Input")

		river = arcpy.Parameter(displayName="Distance to River table", name="river", datatype="DETable",
								  parameterType="Required", direction="Input")

		params = [wells, results, ndep, bioclim, gwdepth, septics, cvhm, lu, river]

		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		# TODO check all parameters have unique ID

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, [config.well_id_field]) is False:
				parameters[0].setErrorMessage("Please add field called '%s' with unique ID numbers" % config.well_id_field)
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# get parameters
		input_pts = parameters[0].valueAsText
		output = parameters[1].valueAsText
		atmo_table = parameters[2].valueAsText
		bioclim_table = parameters[3].valueAsText
		depth_gw = parameters[4].valueAsText
		septics_table = parameters[5].valueAsText
		cvhm_table = parameters[6].valueAsText
		lu_table = parameters[7].valueAsText
		river_table = parameters[8].valueAsText

		#make temp feature layer
		arcpy.MakeFeatureLayer_management(input_pts, "templyr")

		# drop fields from templyr
		# use ListFields to get a list of field objects
		fieldObjList = arcpy.ListFields("templyr")
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
		arcpy.DeleteField_management("templyr", fieldNameList)

		# N dep
		arcpy.AddMessage("Adding N dep Table")
		arcpy.JoinField_management("templyr", config.well_id_field, atmo_table, config.well_id_field, ["MEAN"])
		arcpy.AlterField_management("templyr", "MEAN", "NDEP_MEAN")

		# depth to ground water
		arcpy.AddMessage("Adding N Depth Table")
		arcpy.JoinField_management("templyr", config.well_id_field, depth_gw, config.well_id_field, ["MEAN"])
		arcpy.AlterField_management("templyr", "MEAN", "GWDEPTH_MEAN")

		# number of people on septics
		arcpy.AddMessage("Adding Septics Table")
		arcpy.JoinField_management("templyr", config.well_id_field, septics_table, config.well_id_field, ["SUM"])
		arcpy.AlterField_management("templyr", "SUM", "SEPTICS_NPEOPLE")

		# river distance
		arcpy.AddMessage("Adding distance to major river Table")
		arcpy.JoinField_management("templyr", config.well_id_field, river_table, config.well_id_field, ["NEAR_DIST"])
		arcpy.AlterField_management("templyr", "NEAR_DIST", "RIVER_DISTANCE")

		# climate variables
		arcpy.AddMessage("Adding Bioclim Table")
		rastersux = "_bioclim_1k"
		fields = ["b12", "b13", "b14", "b15", "b16", "b17", "b18", "b19"]
		full_fields = []
		for field in fields:
			full = field + rastersux
			full_fields.append(full)
		arcpy.JoinField_management("templyr", config.well_id_field, bioclim_table, config.well_id_field, full_fields)

		arcpy.AlterField_management("templyr", full_fields[0], "PRECIP_ANNUAL")
		arcpy.AlterField_management("templyr", full_fields[1], "PRECIP_WETMONTH")
		arcpy.AlterField_management("templyr", full_fields[2], "PRECIP_DRYMONTH")
		arcpy.AlterField_management("templyr", full_fields[3], "PRECIP_SEASONALITY")
		arcpy.AlterField_management("templyr", full_fields[4], "PRECIP_WETQUART")
		arcpy.AlterField_management("templyr", full_fields[5], "PRECIP_DRYQUART")
		arcpy.AlterField_management("templyr", full_fields[6], "PRECIP_WARMQUART")
		arcpy.AlterField_management("templyr", full_fields[7], "PRECIP_COLDQUART")

		# soil texture variables
		arcpy.AddMessage("Adding Soil Texture Table")
		soil_fields = ["PC_D25", "PC_D75", "PC_D125", "PC_D175", "PC_D225", "PC_D275", "PC_D325", "PC_D375"]
		arcpy.JoinField_management("templyr", config.well_id_field, cvhm_table, config.well_id_field, soil_fields)

		# landuse groups
		arcpy.AddMessage("Adding Land Use Table")
		lu_fields = ["GROUP_1", "GROUP_2", "GROUP_3", "GROUP_4", "GROUP_5", "GROUP_6", "GROUP_7", "GROUP_8",
		             "GROUP_9", "GROUP_10", "GROUP_11", "GROUP_12", "GROUP_13", "GROUP_AREA"]
		arcpy.JoinField_management("templyr", config.well_id_field, lu_table, config.well_id_field, lu_fields)

		arcpy.AlterField_management("templyr", lu_fields[0], "LU1990_NATURALWATER")
		arcpy.AlterField_management("templyr", lu_fields[1], "LU1990_CITRUSSUBTROP")
		arcpy.AlterField_management("templyr", lu_fields[2], "LU1990_TREEFRUIT")
		arcpy.AlterField_management("templyr", lu_fields[3], "LU1990_NUTS")
		arcpy.AlterField_management("templyr", lu_fields[4], "LU1990_COTTON")
		arcpy.AlterField_management("templyr", lu_fields[5], "LU1990_FIELDCROPS")
		arcpy.AlterField_management("templyr", lu_fields[6], "LU1990_FORAGE")
		arcpy.AlterField_management("templyr", lu_fields[7], "LU1990_ALFALFAPASTURE")
		arcpy.AlterField_management("templyr", lu_fields[8], "LU1990_CAFO")
		arcpy.AlterField_management("templyr", lu_fields[9], "LU1990_VEGBERRY")
		arcpy.AlterField_management("templyr", lu_fields[10], "LU1990_PERIURBAN")
		arcpy.AlterField_management("templyr", lu_fields[11], "LU1990_GRAPES")
		arcpy.AlterField_management("templyr", lu_fields[12], "LU1990_URBAN")
		arcpy.AlterField_management("templyr", lu_fields[13], "LU1990_TOTALAREA")

		# export to table
		arcpy.CopyRows_management("templyr", output)

		# TODO export straight to text file

		return


class dist2river(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Distance to River"
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

		# create temp file
		base, file = os.path.split(input_pts)
		temp = file + "_temp"
		temp_file = os.path.join(base, temp)

		# create copy of the input points since ExtractMultiValues overwrites inputs
		arcpy.AddMessage("Creating temp file: %s" %temp)
		arcpy.FeatureClassToFeatureClass_conversion(input_pts, base, temp)

		# use ListFields to get a list of field objects
		fieldObjList = arcpy.ListFields(temp_file)
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
		arcpy.DeleteField_management(temp_file, fieldNameList)

		# find nearest feature
		arcpy.Near_analysis(temp_file, rivers)

		# export to table
		arcpy.CopyRows_management(temp_file, output_table)

		# remove temporary point file
		arcpy.Delete_management(temp_file)

		return