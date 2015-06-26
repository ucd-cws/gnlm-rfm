__author__ = 'Andy'
import os
import csv
from collections import defaultdict

reclass_file = r"C:\Users\Andy\Documents\gnlm-rfm\data\caml\RECLASS14.csv"

"""
group1 = [1, [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]]
group2 = [2, [300, 301, 302, 303, 304, 305, 306, 308]]
group3 = [3, [400, 401, 402, 403, 405, 406, 407, 408, 409]]
group4 = [4, [412, 413, 414]]
"""

# get groups from csv file in format of group1 = ['1', ['class1', 'class2,etc]
def reclass_groups(reclass_file):
	"""reclass file should be csv file with headers and in the format of from, to"""
	data = defaultdict(list)
	with open(reclass_file, 'rb') as f:
		reader = csv.reader(f)
		next(reader)
		for row in reader:
			data[row[0]].append(row[1])

	groups = []
	for key in data:
		print key, 'corr to', data[key]
		group = (key), data[key]
		groups.append(group)

	return groups

