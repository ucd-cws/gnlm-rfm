# Add dependencies to sys path

import config_paths
import os
import sys
import arcpy

sys.path.insert(0, os.path.join(config_paths.wd, r'dependencies\ArcGISPermanentOneToOneJoin'))
import ArcGISPermanentOneToOneJoin as o2o

source = os.path.join(config_paths.wd, r"results\WELLS_UCD_vars_20160513.mdb")
target_table = os.path.join(source, "GNLM_Nload")

# Set the current workspace
arcpy.env.workspace = source
list_gnlm_tables = arcpy.ListTables('GNLM_Res*')
for table in list_gnlm_tables:
	year = table[8:12]
	var = table[13:]
	new_name = var + '_' + year
	print(new_name)
	o2o.permanent_join(target_table, "WELLID", os.path.join(source, table), "WELLID", "SUM_", new_name)




