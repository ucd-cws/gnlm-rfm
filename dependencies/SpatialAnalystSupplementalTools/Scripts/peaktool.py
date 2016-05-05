import arcpy
from arcpy.sa import *



class Peak(object):
    """Locate the highest points (peaks) in an elevation raster."""
    def __init__(self):
        self.label = "Peak"
        self.description =  ("Locate the highest points (peaks) " +
                            "in an elevation raster.")
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Input parameter
        in_raster = arcpy.Parameter(
            displayName="Input raster",
            name="in_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Output raster parameter
        out_raster = arcpy.Parameter(
            displayName="Output raster",
            name="out_raster",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        # Output point features parameter
        out_points = arcpy.Parameter(
            displayName="Output point features",
            name="out_point_features",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")

        parameters = [in_raster, out_raster, out_points]

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
        return

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        # Retrieve input parameter values and run main.
        elev_raster = Raster(parameters[0].valueAsText)
        out_raster = parameters[1].valueAsText
        output_points = parameters[2].valueAsText

        # Get highest (max) value in the raster.
        max_value = elev_raster.maximum

        # Inverse the raster so peaks become sinks
        inverse_raster = max_value - elev_raster

        # Run flow direction and Sink on inverse raster to isolate
        # areas of interest
        arcpy.env.cellSize = elev_raster.catalogPath
        arcpy.env.snapRaster = elev_raster.catalogPath
        flow_dir = FlowDirection(inverse_raster)
        peak_dem = Sink(flow_dir)

        # Find maximum value with in peak
        zonal_raster = ZonalStatistics(peak_dem, "value", elev_raster, "MAXIMUM")

        # Retrieve all cells in elevation raster equal to zonal raster
        #values (max values).
        con_raster = Con(elev_raster == zonal_raster, elev_raster)
        con_raster.save(out_raster)

        if output_points is not None:

            # Convert the raster cells to point polygon features, then to a
            # point representing the peak - output the highest locations.
            output_feat = "in_memory/feat"
            arcpy.conversion.RasterToPolygon(Int(con_raster), output_feat,
                                            "NO_SIMPLIFY")
            arcpy.management.FeatureToPoint(output_feat, output_points)

        return
