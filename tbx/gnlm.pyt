# ---------------------------------------------------------------------------------------------------
# Name: gnlm.pyt
# Purpose: ArcGIS python toolbox containing geoprocessing tools for the gnlm rfm project
# Author: Andy Bell (ambell@ucdavis.edu)
# Created: 6/25/2015
# ---------------------------------------------------------------------------------------------------

import arcpy
import os
import config

class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "Tools for GNLM RFM"
		self.alias = "Tools for groundwater wells"

		# List of tool classes associated with this toolbox
		self.tools = [WellBuffers, caml]


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

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, ["WELLID"]) is False:
				parameters[0].setErrorMessage("Please add field called 'WELLID' with unique ID numbers")
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
		arcpy.FeatureClassToFeatureClass_conversion(well_points, output, "Points")

		pts = os.path.join(output, "Points")

		# create buffer around points (1.5 miles) and save to results
		#Buffer_analysis (in_features, out_feature_class, buffer_distance_or_field, {line_side}, {line_end_type}, {dissolve_option}, {dissolve_field})
		arcpy.AddMessage("Creating buffers")
		arcpy.Buffer_analysis(pts, os.path.join(output, "buffers"), "1.5 Miles")

		return

class caml(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Tabulate CAML area"
		self.description = "Tabulate area within buffers from CAML landuse"
		self.canRunInBackground = True

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_buffers = arcpy.Parameter(displayName="Input Well buffers", name="well_buffers", datatype="GPFeatureLayer",
								 parameterType="Required")

		well_buffers.filter.list = ["Polygon"]

		results = arcpy.Parameter(displayName="Output location", name="results", datatype="DEWorkspace",
		                          parameterType="Required", direction="Input")

		params = [well_buffers,results]
		return params

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

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

		if parameters[0].value:
			fcs = parameters[0].valueAsText
			if check_fieldnames(fcs, ["WELLID"]) is False:
				parameters[0].setErrorMessage("Please add field called 'WELLID' with unique ID numbers")
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters
		# Parameters
		polygons = parameters[0]
		out = parameters[1]

		well_polygons = polygons.valueAsText
		output = out.valueAsText

		# Import custom toolbox
		arcpy.ImportToolbox(config.sup_tbx)

		# Check out the ArcGIS Spatial Analyst extension license
		arcpy.CheckOutExtension("Spatial")

		# settings from config file
		in_zone_data = well_polygons
		zone_field = "WELLID"
		output = output

		# overwrite output must be set to true in order to get all of the overlapping polygons processed.
		arcpy.env.overwriteOutput = "True"

		years = [1945, 1960, 1975, 1990, 2005]

		for year in years:
			print "Processing CAML: %s" %year
			caml_path = os.path.join(config.gnlmrfm, "data\caml", str(year), "landuse.tif")
			table_name = "CAML_" + str(year)

			# snap raster to caml input
			arcpy.env.snapRaster = caml_path

			# reference tools using tool alias _ tbx alias
			arcpy.TabulateArea02_sas(in_zone_data, zone_field, caml_path, "Value", os.path.join(output, table_name), "50")

		return