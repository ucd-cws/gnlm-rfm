"""Find the maximum upstream elevation along the longest flow path for every
cell on a raster.
in_elevation_raster -- input elevation raster
in_flowdirection_raster -- input flow direction raster
out_raster -- output maximum upstream elevation raster
"""
import sys
import math
import numpy
import arcpy
from arcpy.sa import *

offsetList = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1),
              (-1, -1), (-1, 0), (-1, 1)]
dirList = [1, 2, 4, 8, 16, 32, 64, 128]
diagDirList = [2, 8, 32, 128]
listProcessed = list()

npFlowDir = None
rowElev = None
npOut = None
npOutFL = None
elevNoData = None
fdrNoData = None
currentElev = None
xCZ = None
diagCZ = None
countLoops = 0
loopCancelled = True
fromLongestStream = False

def GetNextCellLocation(current, flowdir):
    """Return next cell in the flow path for a given location."""
    global offsetList
    global dirList
    global fdrNoData
    fdir = flowdir[current]
    if fdir <= 0 or fdir >= 255:
        return -1
    v = math.log(fdir, 2)
    nextc = []
    if int(v) != v:  # splitted flow case
        for b in dirList:
            if fdir & b > 0:  # a valid direction is detected
                base = int(math.log(b, 2))
                offset = offsetList[base]
                temp = (current[0] + offset[0], current[1] + offset[1], b)
                nextc.append(temp)
    else:  # nonsplit flow case
        base = int(v)
        offset = offsetList[base]
        temp = (current[0] + offset[0], current[1] + offset[1], fdir)
        nextc.append(temp)
    return nextc


def IsNextCellFlowBack(flowDir, curCell, nextCell):
    """Find if next cell flows back to an upstream cell.
    If it flows back, then it is a sink."""
    nextPosList = GetNextCellLocation(nextCell, npFlowDir)
    if nextPosList < 0:
        return True
    for pos in nextPosList:
        x = pos[0]
        y = pos[1]
        if curCell[0] == x and curCell[1] == y:
            return True
    return False


def ReadRow(inRas, row_num):
    """Read a row from a raster and return it as a numpy array."""
    a = Raster(inRas)
    cz = a.meanCellHeight
    x = a.extent.XMin
    y = a.extent.YMax - (row_num + 1) * cz
    llc = arcpy.Point(x, y)
    row = arcpy.RasterToNumPyArray(inRas, llc, nrows=1)
    return row

def TraceDownStreamAndReplace1(currentCell):
    """Process a cell by tracing it downstream.
    Assign its elevation along the flow path if larger."""
    global npFlowDir
    global rowElev
    global npOut
    global npOutFL
    global elevNoData
    global fdrNoData
    global currentElev
    global xCZ
    global diagCZ
    global countLoops
    global loopCancelled
    global fromLongestStream

    currentPos = currentCell
    if fromLongestStream:
        currentFlowLen_DS = npOutFL[currentPos]

    try:
        # if invalid flow dir value, exit the loop
        nextPosList = GetNextCellLocation(currentPos, npFlowDir)
        if nextPosList < 0:
            return
        for nextPos in nextPosList:
            x = nextPos[0]
            y = nextPos[1]
            d = nextPos[2]  # direction
            if(x >= 0 and x < npFlowDir.shape[0] and y >= 0 and
               y < npFlowDir.shape[1]):  # check for out of bound
                if npFlowDir[(x, y)] == 0:
                    return

                nextFDir = npFlowDir[(x, y)]
                nextElev = npOut[(x, y)]
                if nextElev == elevNoData: # Exit on NoData
                    return

                if fromLongestStream:
                    nextLen = npOutFL[(x, y)]
                    diagDetect = math.log(d, 2) / 2
                    if int(diagDetect) != diagDetect:
                        currentFlowLen_DS = currentFlowLen_DS + diagCZ
                    else:
                        currentFlowLen_DS = currentFlowLen_DS + xCZ

                    if currentFlowLen_DS <= nextLen:  # stops on a larger elevation
                        return
                    else:  # flow max elevation to next cell if it is larger
                        npOutFL[(x, y)] = currentFlowLen_DS
                        npOut[(x, y)] = currentElev
                        countLoops += 1
                    # stops at sink
                    if IsNextCellFlowBack(npFlowDir, currentPos, (x, y)):
                        return
                else:
                    if currentElev > nextElev:
                        npOut[(x, y)] = currentElev
                        countLoops += 1
                    else:
                        return

                if countLoops > 950:
                    loopCancelled = True
                    return

                TraceDownStreamAndReplace1((x, y))  # recursive call

            else:
                return
    except:
        return


class MaximumUpstreamElevation(object):
    """Tool class for the maximum upstream elevation tool"""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Maximum Upstream Elevation"
        self.description = ("Geoprocessing tool that calculates the maximum " +
                            "upstream elevation along the longest flow " +
                            "path for each cell on an elevation raster.")
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        paramInElev = arcpy.Parameter(name="in_surface_raster",
                                 displayName="Input surface raster",
                                 direction="Input",
                                 datatype="GPRasterLayer",
                                 parameterType="Required")
        paramInFlowDir = arcpy.Parameter(name="in_flow_direction_raster",
                                 displayName="Input flow direction raster",
                                 direction="Input",
                                 datatype="GPRasterLayer",
                                 parameterType="Required")
        paramOutRaster = arcpy.Parameter(name="out_raster",
                                 displayName="Output raster",
                                 direction="Output",
                                 datatype="DERasterDataset",
                                 parameterType="Required")
        paramLongestStreamOnly = arcpy.Parameter(name="longest_upstream",
                                 displayName="Along longest upstream",
                                 direction="Input",
                                 datatype="GPBoolean",
                                 parameterType="Optional")
        paramLongestStreamOnly.value = False
        paramLongestStreamOnly.filter.type = "ValueList"
        paramLongestStreamOnly.filter.list = ["WATERSHED", "LONGEST_STREAM"]

        params = [paramInElev, paramInFlowDir, paramOutRaster, paramLongestStreamOnly]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                #arcpy.CheckOutExtension("Spatial")
                return True # tool can be executed
            else:
                return False
        except:
            return False # tool cannot be executed


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        global npFlowDir
        global rowElev
        global npOut
        global npOutFL
        global elevNoData
        global fdrNoData
        global currentElev
        global xCZ
        global diagCZ
        global countLoops
        global loopCancelled
        global fromLongestStream

        sys.setrecursionlimit(1000)

        inElev = parameters[0].valueAsText
        inFlowDir = parameters[1].valueAsText
        outMaxElev = parameters[2].valueAsText
        longestOnly = parameters[3].value
        fromLongestStream = False
        if (longestOnly == True or longestOnly == "LONGEST_STREAM"):
            fromLongestStream = True
        else:
            fromLongestStream = False

        outFlowLen = "#"

        arcpy.env.overwriteOutput = True

        inElevRas = Raster(inElev)
        elevNoData = inElevRas.noDataValue
        fdrNoData = Raster(inFlowDir).noDataValue

        inRasExt = inElevRas.extent
        x = inRasExt.XMin
        y = inRasExt.YMin
        llc = arcpy.Point(x, y)
        xCZ = inElevRas.meanCellWidth
        yCZ = inElevRas.meanCellHeight
        diagCZ = math.sqrt(xCZ * xCZ + yCZ * yCZ)

        npElev = arcpy.RasterToNumPyArray(inElev)
        npOut = npElev * 1.0
        #del npElev
        npFlowDir = arcpy.RasterToNumPyArray(inFlowDir)
        if fromLongestStream:
            npOutFL = numpy.zeros(npOut.shape, dtype=float)

        arcpy.SetProgressor("step", "Finding max upstream elevation...",
                            0, npFlowDir.shape[0], 1)
        arcpy.SetProgressorLabel("Finding max upstream elevation for {0} "
                                 "cells".format(npFlowDir.shape[0] *
                                                npFlowDir.shape[1]))

        while loopCancelled:
            loopCancelled = False
            for i in xrange(npFlowDir.shape[0]):
                arcpy.SetProgressorPosition(i + 1)
                rowElev = npOut[i]
                #rowElev = ReadRow(inElev, i)[0]
                for j in xrange(npFlowDir.shape[1]):
                    countLoops = 0
                    currentPos = (i, j)
                    currentElev = rowElev[j]
                    if not currentElev == elevNoData: # handle nodata area
                        TraceDownStreamAndReplace1(currentPos)

        inMemOutElev = "in_memory/maxelevtmpz"
        inMemOutFlowL = "in_memory/maxelevfltmpz"

        rasOutElev = arcpy.NumPyArrayToRaster(npOut, llc, xCZ,
                                              yCZ, elevNoData)
        if elevNoData is None:  # when output is FGDB
            rasOutElev = rasOutElev * arcpy.sa.BooleanOr(inElevRas, 1)
        rasOutElev.save(outMaxElev)
        del rasOutElev

        loopCancelled = True

        if not outFlowLen == "#":
            try:
                rasOutFlowL = arcpy.NumPyArrayToRaster(npOutFL, llc, xCZ, yCZ)
                rasOutFlowL.save(outFlowLen)
                del rasOutFlowL
            except Exception:
                pass

        # Free the numpy arrays
        npOutFL = None
        npElev = None
        npOut = None
        npFlowDir = None

