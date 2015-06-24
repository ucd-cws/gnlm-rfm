# ---------------------------------------------------------------------------------------------------
# Name: HistoricalDEM.pyt
# Purpose: ArcGIS python toolbox containing geoprocessing tools for the Delta Historical DEM project
# Author: Andy Bell (ambell@ucdavis.edu)
# Created: 11/20/2014
# ---------------------------------------------------------------------------------------------------

import arcpy
import os
import tab_area


class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "Tools for GNLM RFM"
		self.alias = "Tools for groundwater wells"

		# List of tool classes associated with this toolbox
		self.tools = [RasterizeWellBuffer]


class RasterizeWellBuffer(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Rasterize well Buffer"
		self.description = "Converts each point to a buffered raster"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""

		well_pts = arcpy.Parameter(displayName="Input Well Features", name="well_pts", datatype="GPFeatureLayer",
								 parameterType="Required")

		wellid_field = arcpy.P


		raster_buffer = arcpy.Parameter(displayName="Location for Raster buffer", name="raster_buffer",
		                               datatype="GPRasterLayer", parameterType="Required")

		params = [well_pts, wellid_field, raster_buffer]
		return params

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""

		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""

		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""

		# get parameters from tool

		# check if wellid already exists?

		# buffer 1.5 miles around well

		# append buffer to ouput location // Is there a good way to check that it does not already exist????

		# convert vector buffer into raster (do we need to make sure snap to cells used for GNLM??)

		# append to raster section of gdb

		return


