import arcpy

def permanent_join(target_table, target_attribute, source_table, source_attribute, attribute_to_attach, rename_attribute=None):
	"""
	Provides a way to permanently attach a field to another table, as in a one to one join, but without performing a
	join then exporting a new dataset. Operates in place by creating a new field on the existing dataset.

	Or, in other words, Attaches a field to a dataset in place in ArcGIS - instead of the alternative of doing an
	actual join and then saving out a new dataset. Only works as a one to one join.

	:param target_table: the table to attach the joined attribute to
	:param target_attribute: the attribute in the table to base the join on
	:param source_table: the table containing the attribute to join
	:param source_attribute: the attribute in table2 to base the join on
	:param attribute_to_attach: the attribute to attach to table 1
	:param rename_attribute: string to indicate what to rename the field as when it's joined.
	:return: None
	"""

	if not rename_attribute:
		new_name = source_attribute
	else:
		new_name = rename_attribute

	copy_field_attributes_to_new_field(source_table=source_table, current_field=attribute_to_attach, target_table=target_table, target_field=new_name)

	join_data = read_field_to_dict(source_table, attribute_to_attach, source_attribute)  # look up these values so we can easily just use one cursor at a time - first use the search cursor, then the update cursor on the new table

	updater = arcpy.UpdateCursor(target_table)
	for row in updater:
		if row.getValue(target_attribute) in join_data.keys():  # since we might not always have a match, we need to check, this should speed things up too
			row.setValue(new_name, join_data[row.getValue(target_attribute)])  # set the value for the new field to the other table's value for that same field, indexed by key
			updater.updateRow(row)

	del updater


def copy_field_attributes_to_new_field(source_table, current_field, target_table, target_field):
	"""
		Copies the attributes of a field (data type, precision, scale, length, isNullable, required, domain) to a new field on a new table.
		Correctly maps data types pulled from Describe tool to data types needed for field creation.
	:param source_table: The table containing the existing field
	:param current_field: The field to copy attributes from
	:param target_table: The field to create the new field on
	:param target_field: The name of the new field to create with the attributes from current_field
	:return:
	"""

	# first, we need to find the information about the field that we're attaching
	join_table_fields = arcpy.ListFields(source_table)
	for field in join_table_fields:
		if field.name == current_field:  # we found our attribute
			print(field.name)
			base_field = field
			break
	else:
		raise ValueError("Couldn't find field to base join on in source table")

	type_mapping = {"Integer": "LONG", "OID": "LONG", "SmallInteger": "SHORT",
					"String": "TEXT"}  # ArcGIS annoyingly doesn't report out the same data types as you need to provide, so this allows us to map one to the other

	print("old type: %s" %base_field.type)

	if base_field.type in type_mapping.keys():  # if it's a type that needs conversion
		new_type = type_mapping[base_field.type]  # look it up and save it
	else:
		new_type = base_field.type.upper()  # otherwise, just grab the exact type as specified

	if target_field:
		new_name = target_field
	else:
		new_name = base_field.name

	print("new type: %s" %new_type)

	# copy the field over other than those first two attributes
	arcpy.AddField_management(target_table, new_name, new_type, field.precision, field.scale, field.length,
							  field_alias=None, field_is_nullable=field.isNullable, field_is_required=field.required,
							  field_domain=field.domain)


def read_field_to_dict(input_table, data_field, key_field):
	"""
		Given an arcgis table and a field containing keys and values, reads that field into a dict based on the key field
	:param table: an ArcGIS table (or feature class, etc)
	:param data_field: the field that contains the data of interest - these values will be the dictionary values
	:param key_field: the field that contains the keys/pkey values - these values will be the keys in the dictionary
	:return: dict of the data loaded from the table
	"""

	data_dict = {}

	rows = arcpy.SearchCursor(input_table)
	for row in rows:
		data_dict[row.getValue(key_field)] = row.getValue(data_field)

	del rows

	return data_dict

