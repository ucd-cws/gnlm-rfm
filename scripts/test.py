__author__ = 'Andy'

import tab_area
import time

"""tab_area.polys2rasters(r"C:\Users\Andy\Documents\gnlm-rfm\results\Wells.gdb\Vector\wells_Buffer", "OBJECTID",
              r"C:\Users\Andy\Documents\gnlm-rfm\results\buf  fers.gdb", "50")"""

buffer_folder = r"C:\Users\Andy\Documents\gnlm-rfm\results\buffers.gdb"
caml_1945 = r"C:\Users\Andy\Documents\gnlm-rfm\data\caml\1945\landuse.tif"

buffers = tab_area.get_list_of_rasters(buffer_folder)


start_time = time.time()

#rasterlist, rasterlist_zone_field, in_class_data, class_field, final_out_table, processing_cell_size):
tab_area.rasters_tab_area(buffers, 'Value', caml_1945, 'Value', r"C:\Users\Andy\Documents\gnlm-rfm\results\results.gdb\caml1945", '50')


elapsed_time = time.time() - start_time
elapsed_mins = elapsed_time/60

print "Total processing time (mins):  %s" % elapsed_mins

