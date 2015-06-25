"""Create dendrogram in a PDF file for an input signature file.
in_signature_file -- the input file should have an extension .gsg
out_dendrogram_file -- the output dendrogram (.pdf)
distance_calculation -- whether use variance in the distance calculation
out_text_file -- the output text file containing the distance information
"""
import os
import sys
import math
import arcpy
from pylab import figure
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages

#global variables
acc_order = 0
x0 = 0
y0 = 100
min_Y = y0
step_leaf = 0  # values modified by DendrogramToPDF function
dist_factor = 0
max_distance = 0
total_num_leaves = 0


class Node(object):
    """Defines the node which joins two branches."""
    def __init__(self, data, left, right, level, distance,
                 x=-1, y=-1, pnt=None, lBranch=None,
                 rBranch=None, root=None, weight=1,
                 traversed=False, leafOrder=-1):
        self.data = data
        self.left = left
        self.right = right
        self.level = level
        self.distance = distance
        self.x = x
        self.y = y
        self.pnt = pnt
        self.lBranch = lBranch
        self.rBranch = rBranch
        self.root = root
        self.weight = weight
        self.traversed = traversed
        self.leafOrder = leafOrder

    def CreateBranches(self):
        """Create left and right branches for a node"""
        if self.level > 0:
            #self.distance = self.distance / dist_factor #!!normalize distance
            self.x = self.distance
            self.y = (max([self.left.y, self.right.y])
                      - abs(self.left.y - self.right.y) / 2.0)
            self.pnt = arcpy.Point(self.x, self.y)
            array1 = arcpy.Array()
            array2 = arcpy.Array()
            pnt1 = self.left.pnt
            pnt2 = arcpy.Point(self.x, self.left.y)
            pnt3 = arcpy.Point(self.x, self.right.y)
            pnt4 = self.right.pnt
            array1.add(pnt1)
            array1.add(pnt2)
            array1.add(self.pnt)
            array2.add(self.pnt)
            array2.add(pnt3)
            array2.add(pnt4)
            line1 = arcpy.Polyline(array1)
            line2 = arcpy.Polyline(array2)
            #del self.lines[:]
            self.lBranch = Branch()
            self.lBranch.geo = line1
            self.lBranch.weight = self.left.weight
            self.rBranch = Branch()
            self.rBranch.geo = line2
            self.rBranch.weight = self.right.weight
            self.weight = self.lBranch.weight + self.rBranch.weight
        return


class Branch(object):
    """Define branch in the dendrogram."""
    def __init__(self, geo=None, weight=1):
        self.geo = geo
        self.weight = weight


def TraverseNode(inNode):
    """Traverse nodes and construct points, lines"""
    global acc_order
    global x0
    global y0
    global min_Y
    global step_leaf
    if inNode.traversed is False and inNode.level == 0:
        acc_order += 1
        inNode.leafOrder = acc_order
        inNode.traversed = True
        #construct leaf node point coords
        inNode.x = x0
        inNode.y = y0 - step_leaf * inNode.leafOrder
        if inNode.y < min_Y:  # getting lowest Y
            min_Y = inNode.y
        inNode.pnt = arcpy.Point(inNode.x, inNode.y)
        #inNode.weight = 1
    else:
        if inNode.level > 0 and inNode.traversed is False:
            if inNode.left.traversed is False:
                TraverseNode(inNode.left)
            if inNode.right.traversed is False:
                TraverseNode(inNode.right)
            if inNode.left.traversed and inNode.right.traversed:
                inNode.traversed = True
                inNode.CreateBranches()


def CreateDendrogramPDF(out_text_file, out_pdf_file, in_signature_name):
    """Main function for creating the dendrogram. The dendrogram
    is created using the output text file from the Spatial
    Analyst Dendrogram tool."""
    global acc_order
    global x0
    global y0
    global min_Y
    global step_leaf
    global dist_factor
    global max_distance
    global total_num_leaves

    acc_order = 0
    x0 = 0
    y0 = 100
    min_Y = y0
    step_leaf = 0  # values modified by CreateDendrogramPDF function
    dist_factor = 0
    max_distance = 0
    total_num_leaves = 0

    listPairs = []
    with open(out_text_file) as f:
        readStarted = False
        #readEnded = True
        for line in f:
            if line.strip() == r"-----------------------------------------":
                if readStarted is False:
                    readStarted = True
                else:
                    readStarted = False
                    #f.close()
                    break
            #read pairs to list
            if readStarted:
                listPairs.append(line.strip())

    #remove the first one
    listPairs.pop(0)

    listNodes = []
    nodesStack = []

    #finding class distance value pairs
    listClassDistCleaned = []
    for item in listPairs:
        listClassDist = item.split(" ")
        listTemp = []
        for l in listClassDist:  # clean the empty values
            if not l == "":
                listTemp.append(l)

        listClassDistCleaned.append(listTemp)
        nodesStack.append(-1)  # initialize the nodes stack list
        nodesStack.append(-1)

    #construct all nodes
    #global total_num_leaves
    for a in listClassDistCleaned:
        remainingClass = int(a[0])
        mergedClass = int(a[1])
        distance = float(a[2])
        #Create nodes
        if nodesStack[remainingClass - 1] == -1:  # no previous class in stack
            newLeaf = Node(remainingClass, -1, -1, 0, 0)
            listNodes.append(newLeaf)  # Add new leaf
            total_num_leaves = total_num_leaves + 1
            maxIndex = len(listNodes) - 1
            nodesStack[remainingClass - 1] = maxIndex
            tempLeftNodeIndex = maxIndex
        else:
            tempLeftNodeIndex = nodesStack[remainingClass - 1]

        if nodesStack[mergedClass - 1] == -1:  # no previous class in stack
            newLeaf = Node(mergedClass, -1, -1, 0, 0)
            listNodes.append(newLeaf)  # Add new leaf
            total_num_leaves = total_num_leaves + 1
            maxIndex = len(listNodes) - 1
            nodesStack[mergedClass - 1] = maxIndex

            tempRightNodeIndex = maxIndex
        else:
            tempRightNodeIndex = nodesStack[mergedClass - 1]

        #Add new node to list
        tempLeftNode = listNodes[tempLeftNodeIndex]
        tempRightNode = listNodes[tempRightNodeIndex]
        maxLevel = max(tempLeftNode.level, tempRightNode.level)
        newNode = Node(remainingClass, tempLeftNode,
                       tempRightNode, maxLevel + 1, distance)
        listNodes.append(newNode)

        newMaxIndex = len(listNodes) - 1
        nodesStack[remainingClass - 1] = newMaxIndex  # update stack

    #Finding root node (or deepest node)
    rootNode = listNodes[0]
    for nd in listNodes:
        if nd.level > rootNode.level:
            rootNode = nd

    #global dist_factor
    #global max_distance
    max_distance = rootNode.distance
    dist_factor = max_distance / 16.0

    #global step_leaf
    height_factor = total_num_leaves / 20.0
    step_leaf = 0.2
    y0 = (total_num_leaves + 1) * step_leaf

    #Traverse the node tree to assign orders to the leaves
    #This will assure a correct structure of the tree
    TraverseNode(rootNode)

    #Add the root branch to rootNode
    array1 = arcpy.Array()
    rootEnd = arcpy.Point(rootNode.x + 2, rootNode.y)
    array1.add(rootNode.pnt)
    array1.add(rootEnd)
    root = Branch()
    root.geo = arcpy.Polyline(array1)
    root.weight = rootNode.lBranch.weight + rootNode.rBranch.weight
    rootNode.root = root

    fig_height = (total_num_leaves + 2) * step_leaf
    if fig_height < 5:
        fig_height = 5
    fig = figure(figsize=(7.0, fig_height))
    ax1 = fig.add_subplot(1, 1, 1)

    maxWeight = 0
    for temp in listNodes:  # find max weight
        if temp.level > 0:
            if temp.lBranch.weight > maxWeight:
                maxWeight = temp.lBranch.weight
            if temp.rBranch.weight > maxWeight:
                maxWeight = temp.rBranch.weight
            if temp.root is not None:
                if temp.root.weight > maxWeight:
                    maxWeight = temp.root.weight

    #draw dendrogram
    for node3 in listNodes:
        if node3.level > 0:
            # for lBranch
            p1 = node3.lBranch.geo.getPart(0)
            wt = math.log(math.sqrt(node3.weight))
            if wt <= 0:
                wt = 0.5
            l1 = Line2D([p1[0].X, p1[1].X, p1[2].X],
                        [p1[0].Y, p1[1].Y, p1[2].Y], linewidth=wt)
            ax1.add_line(l1)
            # for rBranch
            p1 = node3.rBranch.geo.getPart(0)
            wt = math.log(math.sqrt(node3.weight))
            if wt <= 0:
                wt = 0.5
            l1 = Line2D([p1[0].X, p1[1].X, p1[2].X],
                        [p1[0].Y, p1[1].Y, p1[2].Y], linewidth=wt)
            ax1.add_line(l1)
            # process root
            if node3.root is not None:
                # for root
                p1 = node3.root.geo.getPart(0)
                wt = math.sqrt(math.log(node3.weight))
                if wt <= 0:
                    wt = 0.5
                l1 = Line2D([p1[0].X, p1[1].X],
                            [p1[0].Y, p1[1].Y], linewidth=wt)
                ax1.add_line(l1)
    del p1

    #Labeling leaves
    for a in listNodes:
        if a.level == 0:
            ax1.text(a.pnt.X, a.pnt.Y, str(a.data) + "   ",
                     ha="right", va="center", size=7)

    #Setting axes props
    ax1.tick_params(labelsize=7)
    ax1.axes.set_xlabel("Distance", size=8)
    ax1.axes.set_ylabel("Classes\n", size=8)
    ax1.spines['left'].set_linewidth(0.5)
    ax1.spines['right'].set_linewidth(0.5)
    ax1.spines['bottom'].set_linewidth(0.5)
    ax1.spines['top'].set_linewidth(0.5)
    ax1.xaxis.grid(True,'major',linewidth=0.5,color='gray')

    #Hide Y tick labels
    for ylabel_i in ax1.get_yticklabels():
        ylabel_i.set_fontsize(0.0)
        ylabel_i.set_visible(False)
    for tick in ax1.get_yticklines():
        tick.set_visible(False)

    #Show X tick labels at top
    ax1.tick_params(labeltop='on', labelright='off')

    ax1.set_xlim(0, max_distance * 1.1)
    ax1.set_ylim(0, y0)

    #Add title
    fig.suptitle("Dendrogram of " + in_signature_name, size=10)

    #save
    pp = PdfPages(out_pdf_file)
    fig.savefig(pp, format='pdf', orientation="portrait", papertype="a4")
    pp.close()


class CreateDendrogram(object):
    """Tool class for create dendrogram"""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Dendrogram"
        self.description = ("Geoprocessing tool that constructs a tree " +
                            "diagram (dendrogram) showing attribute distances" +
                            " between sequentially merged classes" +
                            " in a signature file.")
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        # First parameter
        paramSigFile = arcpy.Parameter(
            displayName="Input signature file",
            name="in_signature_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        paramOutPdf = arcpy.Parameter(
            displayName="Output dendrogram PDF file",
            name="out_dendrogram_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")

        paramUseVar = arcpy.Parameter(
            displayName="Use variance in distance calculations",
            name="distance_calculation",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        paramUseVar.value = True
        paramUseVar.filter.type = "ValueList"
        paramUseVar.filter.list = ["VARIANCE", "MEAN_ONLY"]

        paramOutTxt = arcpy.Parameter(
            displayName="Output dendrogram text file",
            name="out_text_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        params = [paramSigFile, paramOutPdf, paramUseVar, paramOutTxt]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                #arcpy.CheckOutExtension("Spatial")
                return True
            else:
                return False
        except:
            return False # tool cannot be executed
        return True # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        try:
            if parameters[1].valueAsText is not None:
                (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
                if not basenm.endswith(".pdf"):
                    parameters[1].value = os.path.join(
                        dirnm, "{}.pdf".format(basenm))
            if parameters[0].altered:
                if parameters[1].valueAsText is None:
                    parameters[1].value = os.path.join(
                        arcpy.env.scratchFolder, "dendro1.pdf")
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
        in_signature_file = parameters[0].valueAsText
        (sig_dirnm, sig_basenm) = os.path.split(in_signature_file)
        out_pdf_file = parameters[1].valueAsText
        distance_calculation = parameters[2].value
        out_text_file = parameters[3].valueAsText

        no_text_output = False
        out_temp_path = arcpy.env.scratchFolder
        if out_text_file is None:
            no_text_output = True
            uniqueName = arcpy.CreateUniqueName("dendrotmpz", out_temp_path)
            out_text_file = uniqueName + ".txt"

        #overwrite_setting = arcpy.env.overwriteOutput
        if no_text_output:
            arcpy.env.overwriteOutput = True

        distance_calculation2 = ""

        if distance_calculation == True or distance_calculation == "VARIANCE":
            distance_calculation2 = "VARIANCE"

        if distance_calculation == False or distance_calculation == "MEAN_ONLY":
            distance_calculation2 = "MEAN_ONLY"

        arcpy.gp.Dendrogram_sa(in_signature_file, out_text_file,
                                   distance_calculation2, "78")
        # arcpy.env.overwriteOutput = overwrite_setting

        try:
            CreateDendrogramPDF(out_text_file, out_pdf_file, sig_basenm)
        except Exception:
            pass

        #Clean up temp signature file
        if no_text_output:
            try:
                os.remove(out_text_file)
            except Exception:
                pass
