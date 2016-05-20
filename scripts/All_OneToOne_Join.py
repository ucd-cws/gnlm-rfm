# Add dependencies to sys path

import config_paths
import os
import sys
import arcpy

sys.path.insert(0, os.path.join(config_paths.wd, r'dependencies\ArcGISPermanentOneToOneJoin'))
import ArcGISPermanentOneToOneJoin as o2o

source = os.path.join(config_paths.wd, r"results\WELLS_UCD_vars_20160520.mdb")
target_table = os.path.join(source, "UCD_Load")

# Set the current workspace
arcpy.env.workspace = source

# bioclim
bioclim = arcpy.ListTables('BioClim*')
for table in bioclim:
	list_of_fields = arcpy.ListFields(table, "BIO*")
	for field in list_of_fields:
		new_name = "BioClim" + "_" + field.name
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)

# reclassed land use tables

landuse_groups = {'GROUP_1': "natural_water", 'GROUP_2': "citrus_subtropical", 'GROUP_3': "tree_fruit", 'GROUP_4': "nuts", 'GROUP_5': "cotton",
                  'GROUP_6': "field_crops", 'GROUP_7': "forage", 'GROUP_8': "alfalfa_pasture", 'GROUP_9': "cafo", 'GROUP_10': "vegetables_berries",
                  'GROUP_11': "periurban", 'GROUP_12': "grapes", 'GROUP_13': "urban"}

# loop through all the gnlm tables
list_gnlm_tables = arcpy.ListTables('CAML*')
for table in list_gnlm_tables:
	list_of_fields = arcpy.ListFields(table, 'GROUP_*')
	for field in list_of_fields:
		if field.name != "GROUP_AREA":
			group = landuse_groups[str(field.name)]
			new_name = table[:9] + "_" + group
			print(new_name)
			o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)


# dirapp area

dir_groups = {'VALUE_2': "lagoons", 'VALUE_3': "corrals", 'VALUE_1000': "dairy",
                  'VALUE_3000': "fp", 'VALUE_3500': "wwtp", 'VALUE_4000': "biosolids", 'VALUE_6000': "perc"}

area = arcpy.ListTables('DirappArea*')
for table in area:
	list_of_fields = arcpy.ListFields(table, 'Value_*')
	for field in list_of_fields:
		group = dir_groups[str(field.name)]
		new_name = 'DirappArea' + "_" + group
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)

# dirapp raster with kg N per year
dirapp_tables = arcpy.ListTables('Dirapp*')
for table in dirapp_tables:
	list_of_fields = arcpy.ListFields(table, 'SUM_*')
	for field in list_of_fields:
		new_name = table + "_" + "KgNyr"
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)

# dirapp raster with kg N per year
gnlm = arcpy.ListTables('GNLM*')
for table in gnlm:
	list_of_fields = arcpy.ListFields(table, 'N*')
	for field in list_of_fields:
		new_name = table + "_" + field.name
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)



# groundwater depth
depth = arcpy.ListTables("GWDepth")
for table in depth:
	list_of_fields = arcpy.ListFields(table, 'MEAN')
	for field in list_of_fields:
		new_name = table + "_" + field.name
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)


# deposition
ndep = arcpy.ListTables("NDep")
for table in ndep:
	list_of_fields = arcpy.ListFields(table, 'MEAN')
	for field in list_of_fields:
		new_name = table + "_" + field.name
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)


# distance
dist = arcpy.ListTables("RiverDist")
for table in dist:
	list_of_fields = arcpy.ListFields(table, 'NEAR_DIST')
	for field in list_of_fields:
		new_name = table + "_" + "NEAR"
		print(new_name)
		o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", field.name, new_name)
