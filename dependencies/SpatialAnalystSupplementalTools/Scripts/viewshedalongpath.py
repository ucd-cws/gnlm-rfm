"""Compute visibility surface for a line feature. Each vertex on the line
is an observer.
in_raster -- input elevation raster
in_polyline_feature -- the route where the observer travels along
out_raster -- output visibility raster
out_point_features -- the vertices of the polyline feature
z_factor -- the factor for change the Z unit to be the same as XY unit
densify_distance -- add vertices to the polyline
    feature, so that the distance between vertices is less than or equal to this
    distance
observer_offset -- same as observer attribute OFFSETA
inner_radius -- same as RADIUS1
outer_radius -- same as RADIUS2
horizontal_span -- same as (AZIMUTH2 - AZIMUTH1)
vertical_upper_angle -- same as VERT1
vertical_lower_angle -- same as VERT2
"""
import sys
import os
import math
import arcpy
from arcpy.sa import *


class ViewshedAlongPath(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Viewshed Along Path"
        self.description = "This tool computes visibility surface for a route."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name="in_raster",
                                 displayName="Input raster",
                                 direction="Input",
                                 datatype="GPRasterLayer")

        param1 = arcpy.Parameter(name="in_polyline_feature",
                                 displayName="Input polyline feature",
                                 direction="Input",
                                 datatype="GPFeatureLayer")

        param2 = arcpy.Parameter(name="out_raster",
                                 displayName="Output raster",
                                 direction="Output",
                                 datatype="DERasterDataset")

        param3 = arcpy.Parameter(name="out_point_features",
                                 displayName="Output point features",
                                 direction="Output",
                                 datatype="DEFeatureClass",
                                 parameterType="Optional")

        param4 = arcpy.Parameter(name="z_factor",
                                  displayName="Z factor",
                                  direction="Input",
                                  datatype="GPDouble",
                                  parameterType="Optional")
        param4.value = 1.0

        param5 = arcpy.Parameter(name="densify_distance",
                                 displayName="Polyline vertices "
                                 "densification distance",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")

        param6 = arcpy.Parameter(name="observer_offset",
                                 displayName="Observer offset",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        param6.value = 1

        param7 = arcpy.Parameter(name="inner_radius",
                                 displayName="Inner radius",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        param7.value = 0

        param8 = arcpy.Parameter(name="outer_radius",
                                  displayName="Outer radius",
                                  direction="Input",
                                  datatype="GPDouble",
                                  parameterType="Optional")
        param8.value = 2000

        param9 = arcpy.Parameter(name="horizontal_range",
                                 displayName="Horizontal range of scan",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        param9.value = 60

        param10 = arcpy.Parameter(name="vertical_upper_angle",
                                 displayName="Vertical upper angle",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        param10.value = 30

        param11 = arcpy.Parameter(name="vertical_lower_angle",
                                 displayName="Vertical lower angle",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        param11.value = -30

        params = [param0, param1, param2, param3, param4, param5, param6,
                  param7, param8, param9, param10, param11]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("spatial") == "Available":
                #arcpy.CheckOutExtension("spatial")
                return True
            else:
                return False
        except Exception:
            return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        if parameters[4].valueAsText is None:  # z factor
            parameters[4].value = 1.0

        if parameters[6].valueAsText is None:  # obs offset
            parameters[6].value = 1

        if parameters[7].valueAsText is None:  # radius1
            parameters[7].value = 0

        if parameters[8].valueAsText is None:  # radius2
            parameters[8].value = 2000

        if parameters[9].valueAsText is None:  # horiz range
            parameters[9].value = 60

        if parameters[10].valueAsText is None:  # vert1
            parameters[10].value = 30

        if parameters[11].valueAsText is None:  # vert2
            parameters[11].value = -30

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        #Environment settings
        arcpy.env.workspace = "in_memory"
        arcpy.env.scratchWorkspace = "in_memory"
        arcpy.env.overwriteOutput = True
        #Input variables
        in_raster = parameters[0].valueAsText
        in_route = parameters[1].valueAsText
        out_raster = parameters[2].valueAsText
        out_points_fc = parameters[3].valueAsText
        z_factor = parameters[4].value
        in_densify_distance = parameters[5].valueAsText
        obs_height = parameters[6].value
        distance_of_vision1 = parameters[7].value
        distance_of_vision2 = parameters[8].value
        con_of_vision = parameters[9].value
        vertical_angle1 = parameters[10].value
        vertical_angle2 = parameters[11].value

        temp_route = "viewshedr_tmp_"
        temp_points = "viewshedp_tmp_"
        scratch_vertices = "viewshedp2_tmp_"
        #Copy the route to another fc
        arcpy.CopyFeatures_management(in_route, temp_route)

        #Densify the route
        if in_densify_distance is not None:
            arcpy.Densify_edit(temp_route, "DISTANCE",
                               in_densify_distance + " Unknown")

        #Extract the points
        arcpy.FeatureVerticesToPoints_management(temp_route,
                                                 scratch_vertices, "ALL")
        descr1 = arcpy.Describe(scratch_vertices)
        sref = descr1.SpatialReference

        arcpy.CreateFeatureclass_management(arcpy.env.workspace, temp_points,
                                    "POINT", "#", "DISABLED", "DISABLED", sref)

        arcpy.Append_management(scratch_vertices, temp_points,
                                "NO_TEST", "#", "#")

        #Add xy
        arcpy.AddXY_management(temp_points)

        #Add next xy
        for f0 in ["NEXTX","NEXTY"]:
            arcpy.AddField_management(temp_points, f0, "DOUBLE")

        #Calculate values for nextx and nexty
        with arcpy.da.SearchCursor(temp_points, ("POINT_X", "POINT_Y")) as cur:
            list_x = []
            list_y = []
            for row in cur:
                list_x.append(row[0])  # X field
                list_y.append(row[1])  # Y field

        with arcpy.da.UpdateCursor(temp_points, ("NEXTX", "NEXTY")) as cur:
            i = 0
            for row in cur:
                i = i + 1
                if i < len(list_x):
                    row[0] = list_x[i]  # NEXTX field
                    row[1] = list_y[i]  # NEXTY field
                else:
                    row[0] = list_x[i - 1]
                    row[1] = list_y[i - 1]
                cur.updateRow(row)

        #Add and calculate fields
        arcpy.AddField_management(temp_points, "OFFSETA", "DOUBLE")
        arcpy.CalculateField_management(temp_points, "OFFSETA", obs_height)

        for f1 in ["AZIMUTH1", "AZIMUTH2"]:
            arcpy.AddField_management(temp_points, f1, "DOUBLE")

        funcCalculateAzmuth1 = """def CalculateAzmuth1(x, nextx, y, nexty):
            if nextx - x == 0:
                if nexty - y > 0:
                    azm1 = 0 - {0}/2.0
                else:
                    azm1 = 180 - {0}/2.0
            else:
                azm1 = (90.0 - (math.atan((nexty - y) / (nextx - x)) *
                        180 / math.pi + {0}/2.0))
                if (nextx -x) < 0:
                    azm1 = azm1 + 180
            if azm1 < 0:
                azm1 = 360 + azm1
            if azm1 > 360:
                azm1 = azm1 - 360
            return azm1""".format(str(con_of_vision))
        funcCalculateAzmuth2 = """def CalculateAzmuth2(x, nextx, y, nexty):
            if nextx - x == 0:
                if nexty - y > 0:
                    azm2 = 0 + {0}/2.0
                else:
                    azm2 = 180 + {0}/2.0
            else:
                azm2 = (90.0 - (math.atan((nexty - y) / (nextx - x)) *
                        180 / math.pi - {0}/2.0))
                if (nextx -x) < 0:
                    azm2 = azm2 + 180
            if azm2 < 0:
                azm2 = 360 + azm1
            if azm2 > 360:
                azm2 = azm2 - 360
            return azm2""".format(str(con_of_vision))

        try:
            arcpy.CalculateField_management(temp_points, "AZIMUTH1",
                    "CalculateAzmuth1(!point_x!, !nextx!, !point_y!, !nexty!)",
                    "PYTHON_9.3", funcCalculateAzmuth1)
        except Exception:
            pass

        try:
            arcpy.CalculateField_management(temp_points, "AZIMUTH2",
                    "CalculateAzmuth2(!point_x!, !nextx!, !point_y!, !nexty!)",
                    "PYTHON_9.3", funcCalculateAzmuth2)
        except Exception:
            pass

        arcpy.AddField_management(temp_points, "RADIUS1", "DOUBLE")
        arcpy.CalculateField_management(temp_points, "RADIUS1",
                                        distance_of_vision1)

        if distance_of_vision2 is not None:
            arcpy.AddField_management(temp_points, "RADIUS2", "DOUBLE")
            arcpy.CalculateField_management(temp_points, "RADIUS2",
                                            distance_of_vision2)

        for f2 in ["VERT1", "VERT2"]:
            arcpy.AddField_management(temp_points, f2, "DOUBLE")

        arcpy.CalculateField_management(temp_points, "VERT1", vertical_angle1)
        arcpy.CalculateField_management(temp_points, "VERT2", vertical_angle2)

        #Find azimuth1 and azimuth2 for last row
        i = 0
        az1 = 0
        az2 = 0
        with arcpy.da.SearchCursor(temp_points,
        ("OID@", "AZIMUTH1", "AZIMUTH2")) as cur:
            rows = sorted(cur)
            rows.reverse()
            for row in rows:
                i += 1
                if i == 2:
                    az1 = row[1]
                    az2 = row[2]
                    break

        #Update azimuth1 and azimuth2 for last row
        oidfieldname = arcpy.Describe(temp_points).OIDFieldName
        cur = arcpy.UpdateCursor(temp_points, sort_fields=oidfieldname + " D")
        for row in cur:
                row.AZIMUTH1 = az1
                row.AZIMUTH2 = az2
                cur.updateRow(row)
                break
        del cur
        del row

        if out_points_fc is not None:  # point output
            arcpy.CopyFeatures_management(temp_points, out_points_fc)

        arcpy.gp.Viewshed_sa(in_raster, temp_points, out_raster)
        arcpy.ResetEnvironments()
        return
