import os
import sys
import ast
import arcpy
from arcpy.sa import *

def CreateNewExtent(e1,e2):
    extent1 = [float(i) for i in str(e1).split(' ')[:4]]
    extent2 = [float(j) for j in str(e2).split(' ')[:4]]
    maxexts = [max(k) for k in zip(extent1, extent2)]
    minexts = [min(l) for l in zip(extent1, extent2)]
    new_extent = [minexts[0],minexts[1],maxexts[2],maxexts[3]]
    e3 = " ".join("{0:.9f}".format(i) for i in new_extent)
    return e3

def GetEraseValueType(raster,eraseval):
    val = ast.literal_eval(eraseval)
    if arcpy.Describe(raster).isInteger and isinstance(val, float):
        arcpy.AddWarning("Erase value: {} was truncated to match input raster "
                         "pixel type".format(val))
        val = int(val)
    return val

class EraseRasterValues(object):
    """Erase the values of an input raster based on a feature class"""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Erase Raster Values"
        self.description = ("Erase the values of an input raster based on the "
                            "area defined by a feature class or raster.")
        self.canRunInBackground = False
        self.error = 0

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Input parameter [0]
        in_raster = arcpy.Parameter(
            displayName="Input raster",
            name="in_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Input parameter [1]
        in_eraser = arcpy.Parameter(
            displayName="Input erase area feature class or raster",
            name="in_erase_data",
            datatype=["GPFeatureLayer","GPRasterLayer"],
            parameterType="Required",
            direction="Input")

        # Output raster parameter [2]
        out_raster = arcpy.Parameter(
            displayName="Output raster",
            name="out_raster",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        # Input parameter [3]
        erase_value = arcpy.Parameter(
            displayName="Erase value",
            name="erase_value",
            datatype="Variant",
            parameterType="Optional",
            direction="Input")

        erase_value.value = ''

        parameters = [in_raster, in_eraser,out_raster,erase_value]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("spatial") == "Available":
                return True
            else:
                return False
        except Exception:
            return False  # tool cannot be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[3].value:
            if parameters[0].value:
                try:
                    erase_value = ast.literal_eval(parameters[3].valueAsText)
                    if isinstance(erase_value, float) and arcpy.Describe(
                                                 parameters[0].value).isInteger:
                        parameters[3].setWarningMessage("Erase value: {} will "
                        "be truncated to match input raster pixel type".format(
                        parameters[3].value))
                except:
                    parameters[3].setErrorMessage(
                       "Erase Value: {} is invalid".format(parameters[3].value))
        return

    def execute(self, parameters, messages):
        inRaster = parameters[0].valueAsText
        inEraser = parameters[1].valueAsText
        outRaster = parameters[2].valueAsText
        eraseValue = parameters[3].valueAsText

        arcpy.env.overwriteOutput = 1

        pRaster = arcpy.Raster(inRaster)
        dEraser = arcpy.Describe(inEraser)

        if arcpy.env.scratchWorkspace == None:
            arcpy.env.scratchWorkspace = os.path.dirname(outRaster)
        if arcpy.env.extent in [None,'MINOF']:
            arcpy.env.extent = pRaster.extent
        elif arcpy.env.extent == 'MAXOF':
            arcpy.env.extent = CreateNewExtent(pRaster.extent, dEraser.extent)
        if arcpy.env.snapRaster == None:
            arcpy.env.snapRaster = pRaster.catalogPath
        if arcpy.env.cellSize in ['MAXOF','MINOF']:
            arcpy.env.cellSize = pRaster.meanCellHeight
        if arcpy.env.outputCoordinateSystem == None:
            arcpy.env.outputCoordinateSystem = pRaster.spatialReference

        #Create the erase raster:
        if dEraser.datasetType == "FeatureClass":
            arcpy.AddMessage("Converting Features...")
            eRaster01 = arcpy.FeatureToRaster_conversion(inEraser,
                        dEraser.oidFieldName,"#",arcpy.env.cellSize)
        else:
            eRaster01 = inEraser

        # Do the Erase:
        ras01 = IsNull(eRaster01)
        arcpy.AddMessage("Erasing Values...")
        if eraseValue:
            erase_value = GetEraseValueType(inRaster,eraseValue)
            ras02 = Con(ras01,inRaster,erase_value)
        else:
            ras02 = Con(ras01,inRaster,"")
        #Save Final Output
        ras02.save(outRaster)

        return
