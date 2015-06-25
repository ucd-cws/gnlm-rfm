#config file
import os

# location of gnlm-rfm folder
gnlmrfm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# location of spatial analyst supplemental tools
sup_tbx = os.path.join(gnlmrfm, "tbx", "SpatialAnalystSupplementalTools", "Spatial Analyst Supplemental Tools.pyt")

# input data
inputbuffers = r"C:\Users\Andy\Documents\gnlm-rfm\results\Wells.gdb\Vector\wells_Buffer"
config.inputidfield = "WELLID"
output = os.path.join(gnlmrfm, "results\results.gdb")