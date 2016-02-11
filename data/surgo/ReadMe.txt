All layers provided by Toby O'Geen and Mike Walkinshaw. These layers were developed for the UCD SoilWeb App. 	
	
SoilWeb Layer	RF Model Variable(s) to Calculate
Soil organic matter -- units are kg/m2	Average within buffer
	
Ksat mean -- units are micrometers/sec	Average within buffer
	
"Hydrologic group -- 0 = No data, 1 = Group A, 2 = Group B, 3 = Group C, 4 = Group D"	Percent of buffer area that is each group
	(need to write new function within join_dbfs.R to convert?)
Drainage class:	Percent of each area buffer that is each class
Value    Class	(need to write new function within join_dbfs.R to convert?)
0    No data	
2    Well drained	
3    Excessively drained	
4    Somewhat excessively drained	
5    Very poorly drained	
6    Somewhat poorly drained	
7    Poorly drained	
8    Moderately well drained	
