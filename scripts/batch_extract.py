# script to run the analysis in batch

# Import custom toolbox
import arcpy
import config_paths as config

# import gnlm-rfm.pyt
arcpy.ImportToolbox(config.gnlm_rfm_tbx)

# global configs
well_buffers = r"C:\Users\Andy\Documents\nitrates-usgs-rfm\results\tester.mdb\well_buffer_tester"
results_mdb = r"C:\Users\Andy\Documents\nitrates-usgs-rfm\results\tester.mdb"


# CAML GNLM area tabulate tool
print("working on Tabulating CAML area")
years = "1945;1960;1975;1990;2005" # string separated by ;'s
arcpy.caml_gnlm(well_buffers, results_mdb, years)