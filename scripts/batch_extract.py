# script to run the analysis in batch

# Import custom toolbox
import arcpy
import config_paths as config
import os

# import gnlm-rfm.pyt
arcpy.ImportToolbox(config.gnlm_rfm_tbx)

# global configs
well_buffers = os.path.join(config.wd, r"results\tester.mdb\well_buffer_tester")
results_mdb = os.path.join(config.wd, r"results\tester.mdb")

arcpy.env.workspace = os.path.join(config.wd, r"results\temp")


# CAML GNLM area tabulate tool
print("working on Tabulating CAML area")
years = "1945;1960;1975;1990;2005" # string separated by ;'s
arcpy.caml_gnlm(well_buffers, results_mdb, years)


# reclass CAML
print("reclassify")
reclass_csv = os.path.join(wd, r"data\CAML_RECLASS_formated.csv")

# files to process
reclass_dict = []
arcpy.caml_reclass_gnlm(caml_tabulated_table, reclass_csv, output)
