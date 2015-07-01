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
		self.tools = [WellBuffers, caml, caml_reclass, atmo_n, septics]


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

		params = [well_buffers, results]
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

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		#TODO make years selectable? ie toggle boxes?
		years = [1945, 1960, 1975, 1990, 2005] 
		
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