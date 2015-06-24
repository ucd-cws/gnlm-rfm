import arcpy

errorLog = r'C:\Users\Andy\Documents\gnlm-rfm\log.txt'
filePath = errorLog

try:
	print "try"
	arcpy.Delete_management("feat")
	feat

except Exception as e:
	print e.message
	arcpy.AddMessage(arcpy.GetMessages(2)) # see if there is some error there
	try:
		with open(errorLog,'a') as errorMsg:
			errorMsg.write("%s,%s\n" % (wellid, e.message))
	except RuntimeError:
		arcpy.AddMessage("Unable to log")
		arcpy.AddMessage(RuntimeError.message)
