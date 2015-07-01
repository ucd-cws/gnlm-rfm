#config file
import os

# location of gnlm-rfm folder
gnlmrfm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# location of spatial analyst supplemental tools
sup_tbx = os.path.join(gnlmrfm, "tbx", "SpatialAnalystSupplementalTools", "Spatial Analyst Supplemental Tools.pyt")

# well ID field
well_id_field = "WELLID"

# location of the septics raster
septic_raster = os.path.join(gnlmrfm, "data\septics\Septics.tif")

# location of the n dep raster
ndep_raster = os.path.join(gnlmrfm, "data\ndep\ndeposition_bilinear.tif")
