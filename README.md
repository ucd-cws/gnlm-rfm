# gnlm-rfm
random forest model for nitrate loading in groundwater wells


## About

Tools for automating the extration of GNLM data for analysis of groundwater wells in the central valley.


## Methods

Each well is turned in to a seperate polygon using a 1.5 mile radius buffer. Every well should have a unique id "WELLID".



## Tools

List of tools in gnlm-rfm.pyt (an ArcGIS python toolbox). Tools should work in any version of arcgis > 10.0 with the spatial analyst licsence enabled and the
SpatialAnalystSupplementalTools installed ( http://blogs.esri.com/esri/arcgis/2013/01/17/introducing-the-spatial-analyst-supplemental-tools/)

gnlm-rfm.pyt
 - WellBuffers: copies input points to the results geodatabase and creates a 1.5 mile buffer around each well. Important: inputs must have the unique wellid field proir to using the tool
 - caml: tabulates the amount of area within each of the well buffers for each of the caml datasets. Tool unstable with lots of features (reccomend spliting into multiple files if greater than 1k)
 - caml_reclass: summarizes new classes from a csv file and the results of the caml area tool. Useful since it does not require rerunning the tabulate area for each polygon.
 

 Working
 
 - Direct App
 - CVHm soils
 - precip (add value from raster?)
 - Septics (zonal stats avg?)
 - Atmospheric N dep (zonal stats avg?)
 - Depth to groundwater (zonal stats)
 
 
 
 