import arcpy
import collections
import numpy
import os
import sys
import random
import tempfile

class TabulateArea02(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tabulate Area 2"
        self.description = ""


    def getParameterInfo(self):
        """Define parameter definitions"""

        parameters = []

        parameters.append(arcpy.Parameter(
            displayName="Input raster or feature zone data",
            name="in_zone_data",
            datatype=["GPFeatureLayer","GPRasterLayer"],
            parameterType="Required",
            direction="Input"))

        parameters.append(arcpy.Parameter(
            displayName="Zone field",
            name="zone_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"))

        parameters[-1].parameterDependencies = ["in_zone_data"]

        parameters.append(arcpy.Parameter(
            displayName="Input raster or feature class data",
            name="in_class_data",
            datatype=["GPFeatureLayer","GPRasterLayer"],
            parameterType="Required",
            direction="Input"))

        parameters.append(arcpy.Parameter(
            displayName="Class field",
            name="class_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"))

        parameters[-1].parameterDependencies = ["in_class_data"]

        parameters.append(arcpy.Parameter(
            displayName="Output table",
            name="out_table",
            datatype="DETable",
            parameterType="Required",
            direction="Output"))

        parameters.append(arcpy.Parameter(
            displayName="Processing cell size",
            name="cell_size",
            datatype="analysis_cell_size",
            parameterType="Optional",
            direction="input"))

        return parameters

    def isLicensed(self):
        """Execute only if the ArcGIS Spatial Analyst extension is available."""
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                return True
            else:
                return False
        except:
            return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        in_zone_data = parameters[0]
        zone_field = parameters[1]
        in_class_data = parameters[2]
        in_class_field = parameters[3]
        out_table = parameters[4]
        in_cell_size = parameters[5]

        # Default zone field

        #if in_zone_data.value:
        if in_zone_data.altered:
            if not zone_field.altered:
                desc = arcpy.Describe(in_zone_data.value)
                if desc.datasetType == "FeatureClass":
                    zone_field.value = desc.OIDFieldName
                    zone_field.filter.list = ['Short','Long','Text', 'OID']
                else:
                    zone_field.filter.list = ['Short','Long','Text']
                    zone_field.value = "Value" # make this dynamic bc of join

        if (in_class_data.value is not None): #
            desc2 = arcpy.Describe(in_class_data.value)
            if desc2.datasetType == "FeatureClass":
                if hasattr(desc2, 'hasOID'):
                    if desc2.hasOID:
                        in_class_field.value = desc2.OIDFieldName
                        in_class_field.filter.list = ['Short','Long','Text', 'OID']
            else:
                in_class_field.value = "Value" # make this dynamic bc of joins
                in_class_field.filter.list = ['Short','Long','Text']
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, parameters, messages):

        if arcpy.env.overwriteOutput == "False":
            arcpy.env.overwriteOutput = "True"
            owFlag = 1
        else:
            owFlag = 0

        """The source code of the tool."""

        # Parameters
        in_zone_data = parameters[0]
        in_zone_field = parameters[1]
        in_class_data = parameters[2]
        in_class_field = parameters[3]
        out_table = parameters[4]
        in_cell_size = parameters[5]

        # Variables
        feature_class = in_zone_data.valueAsText
        feature_field = in_zone_field.valueAsText
        value_file = in_class_data.valueAsText
        class_field = in_class_field.valueAsText
        output_table = out_table.valueAsText
        cell_size = in_cell_size.valueAsText

        # Create temporary directory
        temp_dir = os.path.join(tempfile.gettempdir(), 'zonal')
        index = 0
        while os.path.exists(temp_dir):
            temp_dir = os.path.join(tempfile.gettempdir(), 'zonal%d' % index)
            index += 1
        os.mkdir(temp_dir)
##        temp_dir = arcpy.env.scratchGDB #[RDB]

        # Initialize variables
        temp_features = os.path.join(temp_dir, "dissolve.shp")
        bldissolved = False
        # Dissolve on non-ObjectID field
        desc = arcpy.Describe(feature_class)
        arcpy.AddMessage("Described zone data")
        if desc.datasetType == "RasterDataset":
            #arcpy.sa.ZonalStatisticsAsTable(in_zone_data, zone_field, \
                #in_value_raster, out_table, ignore_nodata, statistics_type)
            arcpy.sa.TabulateArea(feature_class, feature_field, \
                    value_file, class_field, output_table, cell_size)
            sys.exit()
        if hasattr(desc, "OIDFieldName"):
            if feature_field != desc.OIDFieldName:
                arcpy.Dissolve_management(feature_class, temp_features, \
                    feature_field)
                bldissolved = True
            else:
                temp_features = feature_class
        else:
            arcpy.Dissolve_management(feature_class, temp_features, \
                feature_field)
            bldissolved = True
        # Get ObjectID field from dissolved
        if bldissolved:
            desc = arcpy.Describe(temp_features)
            oid_field = desc.OIDFieldName
        else:
            oid_field = feature_field

        # Calculate polygon contiguity
##        polygon_table = os.path.join(temp_dir, "polygon_table.dbf")
        polygon_table = os.path.join(arcpy.env.scratchGDB, "polygon_table") #[RDB]
        try:
            result = arcpy.PolygonNeighbors_analysis(temp_features, polygon_table, \
            oid_field, "AREA_OVERLAP", "BOTH_SIDES")

            # Retrieve as array with columns src_FID and nbr_FID
            arr = arcpy.da.TableToNumPyArray(polygon_table, \
                ['src_%s' % oid_field, 'nbr_%s' % oid_field])
            arr = numpy.array(arr.tolist())

            # Retrieves the colors of the neighboring nodes
            def get_colors(nodes, neighbors):
                colors = set()
                for neighbor in neighbors:
                    colors.add(nodes[neighbor][0])
                colors.difference([0])
                return colors

            # Create a new color
            def get_new_color(colors):
                return max(colors)+1 if len(colors) > 0 else 1

            # Chooses from existing colors randomly
            def choose_color(colors):
                return random.choice(list(colors))

            # Sort source FIDs in descending order by number of neighbors
            arr_uniq = numpy.unique(arr[:,0])
            arr_count = numpy.zeros_like(arr_uniq)
            for index in range(arr_uniq.size):
                arr_count[index] = numpy.count_nonzero(arr[:, 0] == arr_uniq[index])
            arr_ind = numpy.argsort(arr_count)[::-1]

            # Initialize node dictionary --
            #   where key := FID of feature (integer)
            #   where value[0] := color of feature (integer)
            #   where value[1] := FIDs of neighboring features (set)
            nodes = collections.OrderedDict()
            for item in arr_uniq[arr_ind]:
                nodes[item] = [0, set()]
            # Populate neighbors
            for index in range(arr.shape[0]):
                nodes[arr[index, 0]][1].add(arr[index, 1])

            # Color nodes --
            colors = set()
            for node in nodes:
                # Get colors of neighboring nodes
                nbr_colors = get_colors(nodes, nodes[node][1])
                # Search for a color not among those colors
                choices = colors.difference(nbr_colors)
                # Assign the node that color or create it when necessary
                if len(choices) == 0:
                    new_color = get_new_color(colors)
                    colors.add(new_color)
                    nodes[node][0] = new_color
                else:
                    nodes[node][0] = choose_color(choices)

            # Classify nodes by colors --
            classes = {}
            for node in nodes:
                color = nodes[node][0]
                if color in classes:
                    classes[color].add(node)
                else:
                    classes[color] = set([node])

            # Get set of all FIDs
            all_fids = set()
            with arcpy.da.SearchCursor(temp_features, oid_field) as cursor:
                for row in cursor:
                    all_fids.add(row[0])

            # Add disjoint FIDs to new class if necessary
            disjoint_fids = all_fids.difference(set(nodes.keys()))
            if len(disjoint_fids) > 0:
                new_color = get_new_color(colors)
                classes[new_color] = disjoint_fids

            # Calculate number of classes
            num_classes = len(classes)

            # Perform zonal statistics for each class
            temp_lyr = "temp_layer"
            cl_separator = ' OR \"%s\" = ' % oid_field
            for index, cl in enumerate(classes):
                arcpy.SetProgressorLabel(
                    "Processing layer %d of %d..." % (index+1, num_classes))
                where_clause = '\"%s\" = %s' % (oid_field, \
                    cl_separator.join(map(str, classes[cl])))
                temp_table = os.path.join(temp_dir, "zone_%d.dbf" % index)
                arcpy.MakeFeatureLayer_management(temp_features, temp_lyr, \
                    where_clause)
                try:
                    arcpy.sa.TabulateArea(temp_lyr, feature_field, \
                    value_file, class_field, temp_table, cell_size)
                except:
                    arcpy.GetMessages(0)
            # Merge tables
            arcpy.env.workspace = temp_dir
            table_list = arcpy.ListTables("zone*")
            arcpy.Merge_management(table_list, output_table)
            del table_list

            # Remove temporary directory
            arcpy.Delete_management(temp_dir)

            if owFlag == 1:
                arcpy.env.overwriteOutput = "False"

            return

        except:
            arcpy.sa.TabulateArea(in_zone_data.valueAsText, in_zone_field.valueAsText, in_class_data.valueAsText, in_class_field.valueAsText, out_table.valueAsText, in_cell_size.valueAsText)


