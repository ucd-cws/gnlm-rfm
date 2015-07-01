#config file
import os

# location of gnlm-rfm folder
gnlmrfm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# location of spatial analyst supplemental tools
sup_tbx = os.path.join(gnlmrfm, "tbx", "SpatialAnalystSupplementalTools", "Spatial Analyst Supplemental Tools.pyt")

# well ID field
well_id_field = "WELLID"

