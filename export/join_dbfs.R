# join data to input points for task #2

require(foreign)
require(plyr)

# name of field to join "WELLID" or "GRIDID"
joinfield = "WELLID"

# folder with data (wells or grid)
folder = "wells"

# read in shapefile's dbf with id field as a data table
input_pts <- read.dbf(file.path(folder, "points.dbf"))

# read the dbfs with data
river_distance <- read.dbf(file.path(folder, "RIVER_DISTANCE.dbf"))
bioclim <- read.dbf(file.path(folder, "BIOCLIM.dbf"))
cvhm <- read.dbf(file.path(folder, "CVHM.dbf"))
gwdepth <- read.dbf(file.path(folder, "GWDEPTH.dbf"))
ndep <- read.dbf(file.path(folder, "NDEP.dbf"))
septics <- read.dbf(file.path(folder, "SEPTICS.dbf"))
caml_groups_2005 <-read.dbf(file.path(folder, "CAML_2005_RECLASS.dbf"))

###############

# function to join fields and drop others
join_n_drop <- function(target, table_to_join, by_field, list_of_fields_2_join, list_renamed_fields){
  combined <- join(target, table_to_join, by_field)
  fields_in_target <- names(target)
  fields2keep <- c(fields_in_target, list_of_fields_2_join)
  combined_sub <- combined[fields2keep]
  
  # rename fields using for loop. IMPORTANT length of list_of_fields_2_join must be equal to list_renamed_fields (TODO: write check)!!!
  for(i in 1:length(list_of_fields_2_join)){
    names(combined_sub)[names(combined_sub)==list_of_fields_2_join[i]]<-list_renamed_fields[i]
  }
  joined <- combined_sub
}

caml_area_2_percent <- function(caml_reclass_table){
  caml_reclass_table$GROUP_1 <- caml_reclass_table$GROUP_1/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_2 <- caml_reclass_table$GROUP_2/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_3 <- caml_reclass_table$GROUP_3/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_4 <- caml_reclass_table$GROUP_4/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_5 <- caml_reclass_table$GROUP_5/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_6 <- caml_reclass_table$GROUP_6/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_7 <- caml_reclass_table$GROUP_7/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_8 <- caml_reclass_table$GROUP_8/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_9 <- caml_reclass_table$GROUP_9/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_10 <- caml_reclass_table$GROUP_10/caml_reclass_table$GROUP_AREA 
  caml_reclass_table$GROUP_11 <- caml_reclass_table$GROUP_11/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_12 <- caml_reclass_table$GROUP_12/caml_reclass_table$GROUP_AREA
  caml_reclass_table$GROUP_13 <- caml_reclass_table$GROUP_13/caml_reclass_table$GROUP_AREA
  caml_reclass_table
}
  
###################

# subset input_pts to keep only relevant fields
vars <-c(joinfield, "WELL_NA")
jointarget <- input_pts[vars]

# river distance
jointarget <- join_n_drop(jointarget, river_distance, joinfield, c("NEAR_DIST"), c("RIVER_DISTANCE_m"))

# bioclim
jointarget <- join_n_drop(jointarget, bioclim, joinfield, 
                          c("b12_biocli", "b13_biocli", "b14_biocli", "b15_biocli", "b16_biocli", "b17_biocli", "b18_biocli", "b19_biocli"), 
                          c("annual_precip", "precip_wettest_month", "precip_driest_month", "precip_seasonality", "precip_wet_quart", 
                            "precip_dry_quart", "precip_warm_quart", "precip_cold_quart"))

# cvhm
jointarget <- join_n_drop(jointarget, cvhm, joinfield, c("PC_D25","PC_D75","PC_D125","PC_D175","PC_D225","PC_D275","PC_D325","PC_D375"),
                          c("PC_D25","PC_D75","PC_D125","PC_D175","PC_D225","PC_D275","PC_D325","PC_D375"))

# gwdepth
jointarget <- join_n_drop(jointarget, gwdepth, joinfield, c("MEAN"), c("GROUNDWATER_DEPTH_mean"))

# ndep
jointarget <- join_n_drop(jointarget, ndep, joinfield, c("MEAN"), c("NDEP_mean"))

# septics
jointarget <- join_n_drop(jointarget, septics, joinfield, c("SUM"), c("SEPTICS_numpeople"))

# CAML 2005 groups
caml_groups_2005_percent <- caml_area_2_percent(caml_groups_2005)   # caml results are in meters squared so need to convert to % of group_area

jointarget <- join_n_drop(jointarget,caml_groups_2005_percent, joinfield, c("GROUP_1", "GROUP_2", "GROUP_3", "GROUP_4", "GROUP_5", "GROUP_6", "GROUP_7", "GROUP_8", "GROUP_9", "GROUP_10", "GROUP_11", "GROUP_12", "GROUP_13", "GROUP_AREA"), c("CAML2005_natural", "CAML2005_citrus", "CAML2005_tree", "CAML2005_nuts", "CAML2005_cotton", "CAML2005_field", "CAML2005_forage", "CAML2005_alfalfa", "CAML2005_cafo", "CAML2005_veg", "CAML2005_periurban", "CAML2005_grapes", "CAML2005_urban", "CAML2005_AREA"))

