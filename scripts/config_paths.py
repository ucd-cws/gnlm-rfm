#config file
import os

# location of gnlm-rfm folder
wd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# location of spatial analyst supplemental tools
sup_tbx = os.path.join(wd, "dependencies", "SpatialAnalystSupplementalTools", "Spatial Analyst Supplemental Tools.pyt")

# location of GNLM toolbox
gnlm_rfm_tbx = os.path.join(wd, "scripts", "tbx", "gnlm-rfm.pyt")

# well ID field
well_id_field = "WELLID"

# buffer distance (radius to buffer around a point)
buffer_dist = "1.5 Miles" # If units anything but miles, must change search radius in cvhm

# location of the n dep raster
ndep_raster = os.path.join(wd, r"data\ndep\ndeposition_bilinear.tif")

# location of the groundwater depth raster
dwr_depth_raster = os.path.join(wd, r"data\dwr_gwdepth\DWR_SPRING2012_DTW_m.tif")

# location of bioclim raster
bioclim_raster = os.path.join(wd, r"data\bioclim\bioclim_1k.tif")

# location of cvhm texture centroids
cvhm_centroid_pts = os.path.join(wd, r"data\cvhm\CVHMTexture_Centroids_CA_Teale.shp")

# location of major rivers
major_river = os.path.join(wd, r"data\rivers\NHDFlowlines_major.shp")

# raster template for snapping
snap_template = os.path.join(wd, "data\usgs\raster_template\template.tif")