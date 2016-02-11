#config file
import os

# location of gnlm-rfm folder
gnlmrfm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# location of spatial analyst supplemental tools
sup_tbx = os.path.join(gnlmrfm, "tbx", "SpatialAnalystSupplementalTools", "Spatial Analyst Supplemental Tools.pyt")

# well ID field
well_id_field = "GRIDID"

# buffer distance (radius to buffer around a point)
buffer_dist = "1.5 Miles" # If units anything but miles, must change search radius in cvhm

# location of the septics raster
septic_raster = os.path.join(gnlmrfm, r"data\septics\Septics.tif")

# location of the n dep raster
ndep_raster = os.path.join(gnlmrfm, r"data\ndep\ndeposition_bilinear.tif")

# location of the groundwater depth raster
dwr_depth_raster = os.path.join(gnlmrfm, r"data\dwr_gwdepth\DWR_SPRING2012_DTW_m.tif")

# location of bioclim raster
bioclim_raster = os.path.join(gnlmrfm, r"data\bioclim\bioclim_1k.tif")

# location of cvhm texture centroids
cvhm_centroid_pts = os.path.join(gnlmrfm, r"data\cvhm\CVHMTexture_Centroids_CA_Teale.shp")

# location of major rivers
major_river = os.path.join(gnlmrfm, r"data\rivers\NHDFlowlines_major.shp")

# SURGO soil rasters
som_raster = os.path.join(gnlmrfm, r"data\surgo\om_kg_sq_m.tif")
drain_raster = os.path.join(gnlmrfm, r"data\surgo\drainage_class.tif")
ksat_raster = os.path.join(gnlmrfm, r"data\surgo\mean_ksat.tif")
hydgrp_raster = os.path.join(gnlmrfm, r"data\surgo\hydgrp.tif")