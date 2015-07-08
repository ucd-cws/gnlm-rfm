# r snippit with example of reading in dbf files and joining to original
require(foreign)
require(plyr)

# read in shapefile's dbf with id field as a data table
shp <- read.dbf("wells/points.dbf")

# read in a dbf with data
river_distance <- read.dbf("wells/RIVER_DISTANCE.dbf")

# join data table using ID field
combined <- join(shp, river_distance, by="WELLID")

# subset combined data frame by field name to keep only relevant fields
vars <-c("WELLID", "WELL_NA", "NEAR_DIST")
wells <- combined[vars]

# rename fields 
# df = dataframe, old.var.name = The name you don't like anymore, new.var.name = The name you want to get
# names(df)[names(df) == 'old.var.name'] <- 'new.var.name'

names(wells)[names(wells)=='NEAR_DIST'] <- 'RIVER_DIST_m'

# repeat for all dbfs using for loop?
