# counts all the rows for all tables in a geodatabase
import arcpy
import os

# database
db = r"C:\Users\Andy\Documents\nitrates-usgs-rfm\results\full.mdb"

# Set the current workspace
arcpy.env.workspace = db

# get list of tables
tables = arcpy.ListTables()

# loop through tables
for table in tables:
	print(table)
	cnt = arcpy.GetCount_management(table)
	print(cnt)