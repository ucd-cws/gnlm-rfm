library(maptools)
library(raster)
library(foreign)

# read in dbf from grid points shapefile
dbf <- read.dbf("grid/points_predict.dbf")

# join values using GRIDID as by
predresults <- merge(dbf, predict, by="GRIDID")

# write out dbf back to shapefile
write.dbf(predresults, "grid/points_predict.dbf")


# Load the grid point shapefile
pts <- readShapePoints("grid/points_predict.shp")

# Create a raster, give it the same extent as the points
r <- raster()
extent(r) <- extent(pts)
ncol(r) <- 146 # assign cell size / resolution assuming centroids spaced 1.5miles apart
nrow(r) <- 267

# rasterize the points using the cells of r and values from field in pts
raster <- rasterize(pts, r, pts$prediction) 
plot(raster)

