# CAML 1990 Area

## Files

**Wells_CAML_1990.txt** - tabulated area (in square meters) for all of the CAML 1900 landuse classes within a 1.5 mile radius buffer around each well. Each well can be uniquely identified using the WELLID field (see shapefiles in shps folder).

**Wells_CAML_1990_groups.txt** - the result of summing the tabulated area into the reclassified grouping using a lookup table (CAML_landuse_codes_RECLASS.csv). Each column is the sum of all landuse classes in each group from the tabulated area (units are in square meters). Note: the total area for each well is not uniform since the well buffers may have included areas beyond the extent of the CAML 1990 raster for the Central Valley.

### Reclass Groups
1. Natural and water
2. Citrus and Subtropical
3. Tree Fruit
4. Nuts
5. Cotton
6. Field Crops
7. Forage
8. Alfalfa and Pasture
9. CAFO
10. Vegetables and Berries
11. Peri-Urban
12. Grapes
13. Urban

## Methods
Each well was assigned a unique ID ("WELLID"). The wells were then buffered with a 1.5 mile radius in order to extract the nearby CAML 1990 landuse. The amount of area within each buffer was tabulated using the Tabulate Area 2 Tool from the Spatial Analyst Supplemental Toolbox. The tool calculates cross-tabulated areas between two datasets. Note: edges are assigned using the raster majority rule for each cell. The CAML 1990 land use values were then combined into custom groupings using the custom python tool, Reclass CAML Area From CSV. 
