import sys
import os
import arcpy
myScripts = os.path.join(os.path.dirname(__file__), "Scripts")
sys.path.append(myScripts)


from dendrogrampdf import CreateDendrogram
from viewshedalongpath import ViewshedAlongPath
from maxelevation import MaximumUpstreamElevation
from drawsig import DrawSignatures
from filledcontours import FilledContours
from peaktool import Peak
from eraserastervalues import EraseRasterValues
from zonalstatisticsastable02 import ZonalStatisticsAsTable02
from tabulatearea02 import TabulateArea02

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Spatial Analyst Supplemental Tools"
        self.alias = "sas"

        # List of tool classes associated with this toolbox
        self.tools = [CreateDendrogram,
                      DrawSignatures,
                      ViewshedAlongPath,
                      MaximumUpstreamElevation,
                      FilledContours,
                      Peak,
                      EraseRasterValues,
                      ZonalStatisticsAsTable02,
                      TabulateArea02]

