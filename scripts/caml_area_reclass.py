__author__ = 'Andy'

import arcpy
import os
import csv
from collections import defaultdict

caml_area_file = r"C:\Users\Andy\Documents\gnlm-rfm\results\results_sub.gdb\CAML_1945"
output_path = r"C:\Users\Andy\Documents\gnlm-rfm\results\results_sub.gdb"
reclass_file = r"C:\Users\Andy\Documents\gnlm-rfm\data\caml\RECLASS13.csv"


# get groups from csv file in format of group1 = ['1', ['class1', 'class2,etc]
def reclass_groups(reclass_csv_file):
	"""reclass file should be csv file with headers and in the format of from, to"""
	data = defaultdict(list)
	with open(reclass_file, 'rb') as f:
		reader = csv.reader(f)
		next(reader)
		for row in reader:
			data[row[0]].append(row[1])
	groups = []
	for key in data:
		print key, 'reclass values', data[key]
		group = (key), data[key]
		groups.append(group)
	return groups


def expression(groupclasses, table):
	fieldList = arcpy.ListFields(table) # list of all fields in table
	fields = []
	for field in fieldList:
		fields.append(field.name) # add name to field list

	express = "" # base of the expression
	for item in groupclasses: # iterate over classes or groups
		fieldname = "VALUE_" + str(item)
		if fieldname in fields:
			express = express + '!' + fieldname + '!' + '+'
	express = express[:-1] # removes last plus mark
	return express


def replace_all_null_w_zeros(table):
	fieldList = arcpy.ListFields(table)
	fields = []
	for field in fieldList:
		fields.append(field.name)

	with arcpy.da.UpdateCursor(table, fields) as cursor:
		for row in cursor:
			for i in range(0, len(fields), 1):
				row[i] = row[i] if row[i] else 0  # Use 0 when value is null
			cursor.updateRow(row)


def calc_group(table, group):
	fieldname = "GROUP_" + str(group[0])
	print fieldname
	arcpy.AddField_management(table, fieldname, "DOUBLE")
	try:
		arcpy.CalculateField_management(table, fieldname, expression(group[1], table), "PYTHON_9.3")
	except:
		#arcpy.AddMessage("No values for group... Adding zeros")
		arcpy.CalculateField_management(table, fieldname, 0, "PYTHON_9.3")


def total_area(table, wildcard, areafield):
	# get list of fields that match the wildcard
	fieldlist = arcpy.ListFields(table, wildcard)
	fieldnames = []
	for field in fieldlist:
		fieldnames.append(field.name)

	expr = ""
	for field in fieldlist: # iterate over classes or groups
		expr = expr + '!' + field.name + '!' + '+'
	expr = expr[:-1] # removes last plus mark
	print expr

	arcpy.AddField_management(table, areafield, "DOUBLE")
	try:
		arcpy.CalculateField_management(table, areafield, expr, "PYTHON_9.3")
	except:
		pass


def delete_matching_fields(table, wildcard):
	fieldlist = arcpy.ListFields(table, wildcard)
	fieldnames = []
	for field in fieldlist:
		fieldnames.append(field.name)
	print fieldnames
	arcpy.DeleteField_management(table, fieldnames)
	return


def main(area_table, reclass_csv, output_path, output_name):
	# make a copy of the area table and replace all null values with zeros
	arcpy.TableToTable_conversion(area_table, output_path, output_name)
	outfile = os.path.join(output_path, output_name)
	replace_all_null_w_zeros(outfile)

	# get groups from reclass csv file
	groups = reclass_groups(reclass_csv)

	# sum area for each of the new groups
	for group in groups:
		calc_group(outfile, group)

	# add field with total area
	total_area(outfile, "GROUP_*", "GROUP_AREA")

	# remove old classes
	delete_matching_fields(outfile, "VALUE*")
