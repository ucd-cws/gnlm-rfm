"""Create a filled contour polygon feature class from a surface raster."""
import os
import sys
import arcpy
from arcpy.sa import *


class FilledContours(object):
    """ Create a filled contour polygon feature class from a surface raster."""
    def __init__(self):
        self.label       = "Filled Contours"
        self.description = ("Creates a polygon feature class of filled contours"
                            + " from a raster surface.")

    def getParameterInfo(self):
        """Define the tool tool parameters."""

        # Input Raster parameter
        in_raster = arcpy.Parameter(
            displayName="Input raster",
            name="in_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Output polygon features parameter
        out_polygon_features = arcpy.Parameter(
            displayName="Output polygon features",
            name="out_polygon_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        # Use __file__ attribute to find the .lyr file (assuming the
        # .pyt and .lyr files exist in the same folder).
        out_polygon_features.symbology = os.path.join(os.path.dirname(__file__),
                            '..', 'Layer', 'filledContoursSymbology.lyr')

        # Input contour interval parameter
        contour_interval = arcpy.Parameter(
            displayName="Contour interval",
            name="contour_interval",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        # Input base contour parameter
        base_contour = arcpy.Parameter(
            displayName="Base contour",
            name="base_contour",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        base_contour.value = 0

        # Input Z factor parameter
        z_factor = arcpy.Parameter(
            displayName="Z factor",
            name="z_factor",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        z_factor.value = 1

        parameters = [in_raster, out_polygon_features, contour_interval,
                      base_contour, z_factor]
        return parameters

    def isLicensed(self):
        """Execute only if the ArcGIS Spatial Analyst extension is available."""
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                #arcpy.CheckOutExtension("Spatial")
                return True
            else:
                return False
        except:
            return False # tool cannot be executed
        return True # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[3].valueAsText is None:
            parameters[3].value = 0
        if parameters[4].valueAsText is None:
            parameters[4].value = 1

    def execute(self, parameters, messages):
        """ filled contours main script"""
        def int_if_youCan(x):
            """ Return string without decimals if value has none"""
            if x % 1.0 == 0:
                strX = str(int(x))
            else:
                strX = "%.6f" % (x)
            return strX

        def FindZ(outContoursPolygons, in_raster):
            """ Use the point within the polygon to determine the low and high
                sides of the polygon"""
            outEVT = 'outEVT'
            outEVTjoinedLayer = 'outEVTjoinedLayer'
            outPolygPoints = 'outPolygPoints'
            arcpy.AddMessage("  FeatureToPoint_management...")
            try:
                arcpy.FeatureToPoint_management(outContoursPolygons,
                                                outPolygPoints, 'INSIDE')
            except:
                if arcpy.Describe(
                    outContoursPolygons).spatialReference.name == 'Unknown':
                        arcpy.AddError('This might be caused by data with '+
                                       'Unknown spatial reference.' +
                                       ' Define a projection and re-run')
                sys.exit()
            arcpy.AddMessage("  ExtractValuesToPoints...")
            ExtractValuesToPoints(outPolygPoints, in_raster, outEVT,
                                 'NONE', 'ALL')
            arcpy.MakeFeatureLayer_management(outContoursPolygons,
                                              outEVTjoinedLayer)
            arcpy.AddMessage("  MakeFeatureLayer_management...")
            descFlayer = arcpy.Describe(outEVTjoinedLayer)
            descOutEVT = arcpy.Describe(outEVT)
            arcpy.AddMessage("  AddJoin_management...")
            arcpy.AddJoin_management(outEVTjoinedLayer, descFlayer.OIDFieldName,
                                     outEVT, descOutEVT.OIDFieldName, 'KEEP_ALL')
            return outEVTjoinedLayer, outEVT, outPolygPoints

        def delete_trailing_zeros(strValue):
            """ Remove all the trailing zeros"""
            newStr = strValue
            if '.' in strValue:
                lStr = strValue.split('.')[0]
                rStr = strValue.split('.')[1].rstrip('0')
                newStr = lStr + '.' + rStr
                if rStr == '':
                    newStr = lStr
            return newStr

        def findUniqueContours(inlist):
            """ Find list of unique contours"""
            uniqueContourList = []
            for item in inlist:
                if item not in uniqueContourList:
                    uniqueContourList.append(item)
            return uniqueContourList

        def PerformSpatialJoin(target_fc, join_fc, out_fc, contour_interval):
            """ Perform Spatial Join between contours and filled contours to
                create low and high contour label"""
            try:
                # add a temp field called range
                field = arcpy.Field()
                field.name = "range"
                field.aliasName = "range"
                field.length = 65534
                field.type = "Text"
                # this is the field from where the contour values are coming
                fm = arcpy.FieldMap()
                fm.mergeRule = "Join"
                fm.joinDelimiter = ";"
                fm.addInputField(join_fc, "Contour")
                fm.outputField = field
                # add the field map to the fieldmappings
                fms = arcpy.FieldMappings()
                fms.addFieldMap(fm)
                # add a temp field called elevation
                field = arcpy.Field()
                field.name = "elevation"
                field.aliasName = "Elevation from raster"
                field.type = "Double"
                # this is the field from where raster elevation values are in
                fm2 = arcpy.FieldMap()
                fieldnames = [f.name for f in arcpy.ListFields(target_fc)]
                # find index of elevation field (RASTERVALU) in output
                # created by ExtractValuesToPoints
                rastervalu_index = [index for index, item in
                               enumerate(fieldnames) if 'RASTERVALU' in item][0]
                fm2.addInputField(target_fc, fieldnames[rastervalu_index])
                fm2.outputField = field
                fms.addFieldMap(fm2)
                arcpy.AddMessage("  SpatialJoin_analysis...")
                arcpy.SpatialJoin_analysis(target_fc, join_fc, out_fc, '', '',
                                           fms, 'SHARE_A_LINE_SEGMENT_WITH')
                arcpy.AddMessage("  AddField_management...")
                CreateOutputContourFields(out_fc, contour_interval)

            except Exception as ex:
                arcpy.AddMessage(ex.args[0])

        def CreateOutputContourFields(inFC, contour_interval):
            """ Create and populate the contour fields in the
                                                       output feature class"""
            newFields = ['low_cont',  'high_cont', 'range_cont']
            newFieldAlias = ['Low contour',  'High contour', 'Contour range']
            icnt = 0
            for newField in newFields:
                arcpy.AddField_management(inFC, newField, 'TEXT', '#', '#', '#',
                                          newFieldAlias[icnt], 'NULLABLE',
                                          'REQUIRED', '#')
                icnt+=1

            inFCfields = ['Join_Count', 'range', 'elevation'] + newFields
            with arcpy.da.UpdateCursor(inFC, inFCfields) as cursor:
                for row in cursor:
                    joinCount = row[0]
                    contourString = row[1]
                    pointElevation = row[2]
                    contourList = []
                    for i in contourString.split(';'):
                        contourList.append(float(i))

                    uniquesContours = findUniqueContours(contourList)

                    try:
                        if len(uniquesContours) > 2:
                            contourList = [x for x in contourList if x > -999999]
                        minValue = min(contourList)
                        maxValue = max(contourList)
                        if minValue == maxValue:
                            joinCount = 1
                        if minValue < -999999 or joinCount == 1:
                            if pointElevation > maxValue:
                                minValue = maxValue
                                maxValue = minValue + contour_interval
                            else:
                                minValue = maxValue - contour_interval

                        sminValue = int_if_youCan(minValue)
                        smaxValue = int_if_youCan(maxValue)
                    except:
                        sminValue = int_if_youCan(-1000000)
                        smaxValue = int_if_youCan(-1000000)
                    row[3] = sminValue
                    row[4] = smaxValue
                    row[5] = delete_trailing_zeros(sminValue) + ' - ' + \
                             delete_trailing_zeros(smaxValue)
                    if minValue < -999999:
                        row[5] = '<NoData>'
                    cursor.updateRow(row)

        # Setting variable names for temporary feature classes
        outContours = 'outContours'
        outPolygonBndry = 'outPolygonBndry'
        outContoursPolygons = 'outContoursPolygons'
        outBuffer = 'outBuffer'
        outBufferContourLine = 'outBufferContourLine'
        outBufferContourLineLyr = 'outBufferContourLineLyr'
        outContoursPolygonsWithPoints = 'outContoursPolygonsWithPoints'
        # Input parameters
        in_raster  = parameters[0].valueAsText
        out_polygon_features = parameters[1].valueAsText
        contour_interval = parameters[2].value
        base_contour = parameters[3].value
        z_factor = parameters[4].value

        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
        arcpy.env.workspace = arcpy.env.scratchWorkspace

        outFCext = os.path.splitext(out_polygon_features)
        if (os.path.splitext(out_polygon_features)[1]).lower() == ".shp":
            arcpy.AddError("Only file geodatabase output is supported.")
            sys.exit()

        ras_DEM = Raster(in_raster)
        ras_cellsize = ras_DEM.meanCellHeight

        arcpy.AddMessage("  Contour...")
        arcpy.sa.Contour(in_raster, outContours, contour_interval, base_contour,
                         z_factor)

        arcpy.AddMessage("  RasterToPolygon_conversion...")
        arcpy.RasterToPolygon_conversion(IsNull(ras_DEM), outPolygonBndry,
                                         "NO_SIMPLIFY")
        arcpy.AddMessage("  Buffer_analysis...")
        try:
            arcpy.Buffer_analysis(outPolygonBndry, outBuffer, str(-ras_cellsize)
                                  + ' Unknown', 'FULL', 'ROUND', 'NONE', '#')
        except:
            arcpy.AddError('This might be caused by insufficient memory.'+
                            'Use a smaller extent or try another computer.')
            arcpy.Delete_management(outContours)
            arcpy.Delete_management(outPolygonBndry)
            sys.exit()

        arcpy.AddMessage("  FeatureToLine_management...")
        arcpy.FeatureToLine_management([outContours, outBuffer],
                                        outBufferContourLine, '#', 'ATTRIBUTES')

        arcpy.MakeFeatureLayer_management(outBufferContourLine,
                                          outBufferContourLineLyr)
        arcpy.SelectLayerByAttribute_management(outBufferContourLineLyr,
                                                'NEW_SELECTION',
                                                '"BUFF_DIST" <> 0')
        arcpy.CalculateField_management(outBufferContourLineLyr, 'Contour',
                                        '-1000000', 'VB', '#')
        arcpy.SelectLayerByAttribute_management(outBufferContourLineLyr,
                                                'CLEAR_SELECTION')

        arcpy.AddMessage("  FeatureToPolygon_management...")
        arcpy.FeatureToPolygon_management([outBuffer, outContours],
                                          outContoursPolygons, '#',
                                          'NO_ATTRIBUTES', '#')
        outContoursPolygonsWithPoints, outEVT, outPolygPoints = \
                                           FindZ(outContoursPolygons, in_raster)

        # Spatial Join and update contour labels
        PerformSpatialJoin(outContoursPolygonsWithPoints,
                           outBufferContourLineLyr, out_polygon_features,
                           contour_interval)

        fields = arcpy.ListFields(out_polygon_features)
        fields2delete = []
        for field in fields:
            if not field.required:
                fields2delete.append(field.name)
        arcpy.AddMessage("  DeleteField_management...")
        # these fields include all the temp fields like
        # 'Join_Count', 'TARGET_FID', 'range', and 'elevation'
        arcpy.DeleteField_management(out_polygon_features, fields2delete)

        arcpy.AddMessage('  Deleting temp files.')
        arcpy.Delete_management(outBuffer)
        arcpy.Delete_management(outContours)
        arcpy.Delete_management(outContoursPolygons)
        arcpy.Delete_management(outBufferContourLine)
        arcpy.Delete_management(outPolygonBndry)
        arcpy.Delete_management(outEVT)
        arcpy.Delete_management(outPolygPoints)