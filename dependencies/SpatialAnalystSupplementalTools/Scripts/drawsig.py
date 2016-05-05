"""Create ellipses in a PDF file for the classes in an input signature file.
in_signature_file -- the input file should have an extension .gsg
out_ellipses -- the output ellipses file (.pdf)
n_std -- number of standard deviations to be multiplied
    to the size of the ellipses
show_classid -- whether the class ids will be shown or not at the center of the
    ellipses
"""
import numpy
import math
import os
import arcpy
from arcpy.sa import *
from numpy import linalg as LA
from pylab import figure
from matplotlib.patches import Ellipse
from matplotlib.backends.backend_pdf import PdfPages

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx


def BlockRead(lines, titleStr, startPos, numLines):
    """Read a signature file into memory and return lists"""
    finalList = []
    leadLine = 0
    for l in lines:
        if(l[0:len(titleStr)].lower() == titleStr.lower() and
           leadLine >= startPos):
            break
        leadLine += 1
    for j in xrange(numLines):
        vals = lines[j + 1 + leadLine]
        templist0 = vals.split(" ")
        templist = []
        for v in templist0:
            if not v == "":
                templist.append(v)
        finalList.append(templist)
    return finalList


def ConvertCovarianceToNumPy(cov0):
    """Convert covariance matrix into numpy array"""
    # process classes
    for l in cov0:
        del l[0]
    cov_work = []
    for row in cov0:
        temp = []
        for col in row:
            temp.append(float(col))
        cov_work.append(temp)
    cov_np = numpy.array(cov_work)  # np for class 1
    return cov_np


def CreateEllipseFromCov(bd1, bd2, classCovNp, classMeans, nstd):
    """Return ellipse object for a class in a given band combination"""
    cov_np = classCovNp
    cov_np_sub = numpy.zeros((2, 2))
    cov_np_sub[0][0] = cov_np[bd1][bd1]
    cov_np_sub[0][1] = cov_np[bd1][bd2]
    cov_np_sub[1][0] = cov_np[bd2][bd1]
    cov_np_sub[1][1] = cov_np[bd2][bd2]
    #compute eigenvalues
    (w, v) = LA.eig(cov_np_sub)
    centroid = (float(classMeans[0][bd1]), float(classMeans[0][bd2]))
    orient_arc = math.atan2(v[1][1], v[0][1])
    if w[0] < 0:
        w[0] = 0
    if w[1] < 0:
        w[1] = 0
    wid_hei = (nstd * math.sqrt(w[1]), nstd * math.sqrt(w[0]))
    ell = Ellipse(xy=centroid, width=wid_hei[0], height=wid_hei[1],
                  angle=orient_arc * 180 / math.pi)
    return ell


def GetEllipseBBox(e):
    """Return the bounding extent for an ellipse"""
    majax = e.width / 2.0
    minax = e.height / 2.0
    rad = math.sqrt((majax) ** 2 + (minax) ** 2)
    #majax = max(majax, minax)
    (x, y) = e.center
    ang = e.angle * math.pi / 180.0
    if ang < 0:
        ang = - ang
    if ang > math.pi:
        ang = ang - math.pi
    if ang > math.pi / 2.0:
        ang = math.pi - ang
    inner_ang = math.atan2(minax, majax)
    offs_x = abs(rad * math.cos(ang - inner_ang))
    offs_y = abs(rad * math.cos(math.pi / 2.0 - ang - inner_ang))
    xmax = x + offs_x
    ymax = y + offs_y
    xmin = x - offs_x
    ymin = y - offs_y
    return (min(xmin, xmax), min(ymin, ymax), max(xmin, xmax), max(ymin, ymax))


class DrawSignatures(object):
    """Draw signatures tool class"""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Draw Signatures"
        self.description = ("Geoprocessing tool that draws ellipses to" +
                            " represent classes from a signatures file.")
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        paramSigFile = arcpy.Parameter(name="in_signature_file",
                                 displayName="Input signature file",
                                 direction="Input",
                                 datatype="DEFile",
                                 parameterType="Required")
        paramOutEll = arcpy.Parameter(name="out_ellipses",
                                 displayName="Output ellipses PDF file",
                                 direction="Output",
                                 datatype="DEFile",
                                 parameterType="Required")
        paramNStd = arcpy.Parameter(name="n_std",
                                 displayName="Number of standard "
                                 "deviations",
                                 direction="Input",
                                 datatype="GPDouble",
                                 parameterType="Optional")
        paramNStd.value = 1.0
        paramShowID = arcpy.Parameter(name="show_classid",
                                 displayName="Show class id",
                                 direction="Input",
                                 datatype="GPBoolean",
                                 parameterType="Optional")
        paramShowID.value = True
        paramShowID.filter.type = "ValueList"
        paramShowID.filter.list = ["CLASSID", "NO_CLASSID"]
        params = [paramSigFile, paramOutEll, paramNStd, paramShowID]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].valueAsText is None:
            parameters[2].value = 1.0
        if parameters[2].value <= 0:
            parameters[2].value = 1.0

        try:
            if parameters[1].valueAsText is not None:
                (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
                if not basenm.endswith(".pdf"):
                    parameters[1].value = os.path.join(
                        dirnm, "{}.pdf".format(basenm))
            if parameters[0].altered:
                if parameters[1].valueAsText is None:
                    parameters[1].value = os.path.join(
                        arcpy.env.scratchFolder, "drawsig1.pdf")
        except Exception:
            pass

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:
            if parameters[0].valueAsText is not None:
                (dirnm, basenm) = os.path.split(parameters[0].valueAsText)
                if not basenm.endswith(".gsg"):
                    parameters[0].setErrorMessage("Invalid input file. "
                                                  "A signature file (.gsg) "
                                                  "is expected.")
        except Exception:
            pass

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        #parse the signature file
        signature = parameters[0].valueAsText
        (sig_dirnm, sig_basenm) = os.path.split(signature)
        outpdf = parameters[1].valueAsText
        n_std = parameters[2].value
        showIDs = parameters[3].value

        sig_file = open(signature)
        sig_data = sig_file.read()
        sig_lines = sig_data.split("\n")  # list of lines

        numBands = None
        listIDs = []
        listMeans = []
        #listNames = []
        listNCells = []
        listCov = []

        #read sig file to lists
        for i in xrange(len(sig_lines)):
            if sig_lines[i][0:7].lower() == "#  type":
                numBands = int(BlockRead(sig_lines, "#  type", i, 1)[0][2])
            if sig_lines[i][0:11].lower() == "#  class id":
                listRes = BlockRead(sig_lines, "#  class id", i, 1)
                listIDs.append(listRes[0][0])
                listNCells.append(listRes[0][1])
            if sig_lines[i][0:7].lower() == "# means":
                listRes = BlockRead(sig_lines, "# means", i, 1)
                listMeans.append(listRes)
            if sig_lines[i][0:12].lower() == "# covariance":
                listRes = BlockRead(sig_lines, "# covariance", i, numBands)
                listCov.append(listRes)

        listCovNp = []  # list of covariance in NumPy
        for cov in listCov:
            listCovNp.append(ConvertCovarianceToNumPy(cov))

        # Get unique band combinations
        listComb = []
        for i in xrange(numBands):
            for j in xrange(i + 1, numBands):
                listComb.append([i + 1, j + 1])

        # Create ellipses for each band combination
        listElls = []
        for bd in listComb:
            bd1 = bd[0] - 1
            bd2 = bd[1] - 1
            temp = []
            j = 0
            for clsCov in listCovNp:
                mean = listMeans[j]
                numCells = listNCells[j]
                ell = CreateEllipseFromCov(bd1, bd2, clsCov, mean, n_std)
                temp.append(ell)
                j += 1
            listElls.append(temp)

        # prepare for colors
        jet = cm = plt.get_cmap('jet')
        cNorm = colors.Normalize(vmin=0, vmax=len(listIDs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

        numPlots = len(listComb)
        numRows = numPlots / 2
        fig = figure(figsize=(7.0, (numRows + 1) * 3.0))

        # loop through each band combination
        j = 1
        for bd in listComb:
            bd1 = bd[0] - 1
            bd2 = bd[1] - 1
            ax1 = fig.add_subplot(numRows + 1, 2, j)
            ells = listElls[j - 1]
            j += 1

            #ells = listElls[1]
            xminList = []
            xmaxList = []
            yminList = []
            ymaxList = []
            i = 0
            for e in ells:
                ax1.add_artist(e)
                e.set_facecolor('none')
                rgbClr = scalarMap.to_rgba(i)
                e.set_edgecolor(rgbClr)
                e.set_linewidth(0.5)
                #plot center of ellipse
                ax1.plot(e.center[0], e.center[1], '+', color=rgbClr)
                if showIDs == True or showIDs == "CLASSID":
                    ax1.text(e.center[0], e.center[1], listIDs[i],
                             color=rgbClr, size=6)
                #get bounding boxes
                b = GetEllipseBBox(e)
                xminList.append(b[0])
                yminList.append(b[1])
                xmaxList.append(b[2])
                ymaxList.append(b[3])
                i += 1

            xmin = min(xminList)
            xmax = max(xmaxList)
            ymin = min(yminList)
            ymax = max(ymaxList)

            ax1.tick_params(labelsize=7)
            ax1.axes.set_xlabel("Band " + str(bd1 + 1), size=7)
            ax1.axes.set_ylabel("Band " + str(bd2 + 1), size=7)
            ax1.spines['left'].set_linewidth(0.5)
            ax1.spines['right'].set_linewidth(0.5)
            ax1.spines['bottom'].set_linewidth(0.5)
            ax1.spines['top'].set_linewidth(0.5)
            ax1.grid(True, 'major', ls='dotted', lw=0.1, color='gray')
            #ax1.grid(True, 'minor', ls='dotted', lw=0.1, color='gray')

            ax1.set_xlim(xmin, xmax)
            ax1.set_ylim(ymin, ymax)

        fig.suptitle("Ellipses of " + sig_basenm, size=10)
        #save
        pp = PdfPages(outpdf)
        fig.savefig(pp, format='pdf', orientation="portrait", papertype="a4")
        pp.close()
        return
