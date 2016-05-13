import os
import config_paths as config
import glob

import arcpy

# import gnlm-rfm.pyt
arcpy.ImportToolbox(config.gnlm_rfm_tbx)

# where are the result rasters?
gnlm_results = r"X:\Nitrates2015\results\simulated_land_20160104"
gnlm_result_rasters = glob.glob(os.path.join(gnlm_results, '*', '*.tif'))

print("Total number of rasters to process: %s" %(len(gnlm_result_rasters)))


# buffer
buffer = os.path.join(config.wd, "results", "full.mdb", "wells_20160502_buffer500m")
# where to save the files?
output = os.path.join(config.wd, "results", "full.mdb")

for raster in gnlm_result_rasters:
    raster_path = raster # full path to raster on X drive
    raster_base = os.path.basename(raster) # ie donot_sync_GNLM_Res2050_Nseptic.tif
    wo_ext = os.path.splitext(raster_base)[0] # id donot_sync_GNLM_Res2050_Nseptic
    name = wo_ext[11:] # ie GNLM_Res2050_Nseptic
    print(name)
    arcpy.dirappnload_gnlm(buffer, raster, os.path.join(output, name))  # [well_buffers, raster, results]



