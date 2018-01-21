# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TOMsSnapTrace
                                 A QGIS plugin
 snap and trace functions for TOMs. NB Relies to having single type geometries
                              -------------------
        begin                : 2017-12-15
        git sha              : $Format:%H$
        copyright            : (C) 2017 by TH
        email                : th@mhtc.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox

from qgis.core import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from TOMs_Snap_Trace_dialog import TOMsSnapTraceDialog
import os.path


class TOMsSnapTrace:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TOMsSnapTrace_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TOMsSnapTrace')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'TOMsSnapTrace')
        self.toolbar.setObjectName(u'TOMsSnapTrace')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TOMsSnapTrace', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = TOMsSnapTraceDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TOMsSnapTrace/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Snap and Trace'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&TOMsSnapTrace'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                self.dlg.baysLayer.addItem( layer.name(), layer )
                self.dlg.linesLayer.addItem( layer.name(), layer )
                self.dlg.gnssPointsLayer.addItem( layer.name(), layer )
                self.dlg.kerbLayer.addItem(layer.name(), layer)
                # self.dlg.layerValues.addItem( layer.name(), layer )


        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            # Set up variables to layers - maybe obtained from form ??

            """indexBaysLayer = self.dlg.baysLayer.currentIndex()
            Bays = self.dlg.baysLayer.itemData(indexBaysLayer)

            indexLinesLayer = self.dlg.linesLayer.currentIndex()
            Lines = self.dlg.linesLayer.itemData(indexLinesLayer)

            indexGNSSPointsLayer = self.dlg.gnssPointsLayer.currentIndex()
            GNSS_Points = self.dlg.gnssPointsLayer.itemData(indexGNSSPointsLayer)

            indexsKerbLayer = self.dlg.kerbLayer.currentIndex()
            Kerbline = self.dlg.kerbLayer.itemData(indexsKerbLayer)"""
            
            tolerance =  self.dlg.fld_Tolerance.text()

            Bays = QgsMapLayerRegistry.instance().mapLayersByName("Bays")[0]
            Lines = QgsMapLayerRegistry.instance().mapLayersByName("Lines")[0]
            GNSS_Points = QgsMapLayerRegistry.instance().mapLayersByName("gnssPts_180117")[0]
            Kerbline = QgsMapLayerRegistry.instance().mapLayersByName("EDI_RoadCasement_Polyline")[0]

            if not tolerance:
                tolerance = 0.5
            QgsMessageLog.logMessage("Tolerance = " + str(tolerance), tag="TOMs panel")

            # Snap nodes to GNSS points ...
            # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

            # Set up list of layers to be processed

            listRestrictionLayers = [Bays, Lines]

            QgsMessageLog.logMessage("********** Removing short lines", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.removeShortLines(currRestrictionLayer, 0.25)

            QgsMessageLog.logMessage("********** Removing duplicate points", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.removeDuplicatePoints(currRestrictionLayer, 0.25)

            QgsMessageLog.logMessage("********** Snapping nodes to GNSS points", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.snapNodes(currRestrictionLayer, GNSS_Points, tolerance)
                
            # Snap end points together ...  (Perhaps could use a double loop here ...)
            QgsMessageLog.logMessage("********** Snapping lines to bays ...", tag="TOMs panel")
            self.snapNodes(Lines, Bays, tolerance)

            QgsMessageLog.logMessage("********** Snapping bays to bays ...", tag="TOMs panel")
            self.snapNodes(Bays, Bays, tolerance)

            QgsMessageLog.logMessage("********** Snapping lines to lines ...", tag="TOMs panel")
            self.snapNodes(Lines, Lines, tolerance)

            # Now snap vertices to the kerbline
            QgsMessageLog.logMessage("********** Snapping vertices to kerb ...", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.snapVertices (currRestrictionLayer, Kerbline, tolerance)
            
            # Now trace ...
            # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)
            QgsMessageLog.logMessage("********** Tracing kerb ...", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.TraceRestriction (currRestrictionLayer, Kerbline, tolerance)
           
            # Set up all the layers - in init ...
 
    def snapNodes(self, sourceLineLayer, snapPointLayer, tolerance):

        QgsMessageLog.logMessage("In snapNodes", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Snap node to nearest point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():
            #geom = feat.geometry()
            #attr = feat.attributes()

            currPoint = self.getStartPoint(currRestriction)
            currVertex = 0
            #QgsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), tag="TOMs panel")

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)   # returned as QgsFeature

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("SnapNodes: Moving start point for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")

                geomNearestPt = nearestPoint.geometry().asPoint()
                nearestGeom = currRestriction.geometry()
                moveStatus = nearestGeom.moveVertex(geomNearestPt.x(), geomNearestPt.y(),
                                                    currVertex)
                QgsMessageLog.logMessage("SnapNodes1. Moving status " + str(moveStatus),
                                         tag="TOMs panel")
                # currRestriction.geometry().moveVertex(nearestPoint, currVertex)

            currPoint = self.getEndPoint(currRestriction)

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("SnapNodes: Moving end point for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")
                geomNearestPt = nearestPoint.geometry().asPoint()
                nearestGeom = currRestriction.geometry()
                moveStatus = nearestGeom.moveVertex(geomNearestPt.x(), geomNearestPt.y(),
                                                    currVertex)
                QgsMessageLog.logMessage("SnapNodes2. Moving status " + str(moveStatus),
                                         tag="TOMs panel")

        editCommitStatus = sourceLineLayer.commitChanges()

        reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for commit to " + sourceLineLayer.name() + " is: " + str(
                                            editCommitStatus),
                                        QMessageBox.Ok)

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

        return

    def snapVertices(self, sourceLineLayer, snapLineLayer, tolerance):
        # For each vertex within restriction, get nearest point on snapLineLayer ...
        QgsMessageLog.logMessage("In snapVertices. Snapping " + sourceLineLayer.name() + " to " + snapLineLayer.name(), tag="TOMs panel")
        QgsMessageLog.logMessage("In snapVertices. " + str(sourceLineLayer.featureCount()) + " features in " + sourceLineLayer.name(), tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        for currRestriction in sourceLineLayer.getFeatures():

            QgsMessageLog.logMessage(
                "In snapVertices. Considering " + str(currRestriction.attribute("GeometryID")),
                tag="TOMs panel")

            geom = currRestriction.geometry()
            for vertexNr, vertexPt in enumerate(geom.asPolyline()):

                nearestPoint = self.findNearestPointL(vertexPt, snapLineLayer, tolerance)

                if nearestPoint:
                    # Move the vertex
                    QgsMessageLog.logMessage("Moving vertex " + str(vertexNr) + " for " + str(currRestriction.attribute("GeometryID")),
                                             tag="TOMs panel")
                    QgsMessageLog.logMessage("Moving from  " + str(vertexPt.x()) + " " + str(vertexPt.y()) + " to " + str(nearestPoint.asPoint().x()) + " " + str(nearestPoint.asPoint().y()),
                                             tag="TOMs panel")
                    moveStatus = geom.moveVertex(nearestPoint.asPoint().x(), nearestPoint.asPoint().y(), vertexNr)
                    #moveStatus = sourceLineLayer.moveVertex(nearestPoint.asPoint().x(), nearestPoint.asPoint().y(), currRestriction.id(), vertexNr)
                    QgsMessageLog.logMessage("Moving status " + str(moveStatus),
                                             tag="TOMs panel")

        editCommitStatus = sourceLineLayer.commitChanges()

        #editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)


    def findNearestPointP(self, searchPt, pointLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the given point layer
        # returns QgsPoint
        #QgsMessageLog.logMessage("In findNearestPoint - pointLayer", tag="TOMs panel")

        searchRect = QgsRectangle(searchPt.x() - tolerance,
                                  searchPt.y() - tolerance,
                                  searchPt.x() + tolerance,
                                  searchPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        shortestDistance = float("inf")
        #nearestPoint = QgsPoint()

        # Loop through all features in the layer to find the closest feature
        for f in pointLayer.getFeatures(request):
            # Add any features that are found should be added to a list

            QgsMessageLog.logMessage("findNearestPointP: nearestPoint geom type: " + str(f.geometry().wkbType()), tag="TOMs panel")
            dist = f.geometry().distance(QgsGeometry.fromPoint(searchPt))
            if dist < shortestDistance:
                #QgsMessageLog.logMessage("findNearestPointP: found 'nearer' point", tag="TOMs panel")
                shortestDistance = dist
                #nearestPoint = f.geometry()
                nearestPoint = f

        #QgsMessageLog.logMessage("In findNearestFeatureAt: shortestDistance: " + str(shortestDistance), tag="TOMs panel")


        if shortestDistance < float("inf"):
            #QgsMessageLog.logMessage("nearestPoint: " + str(nearestPoint), tag="TOMs panel")
            #QgsMessageLog.logMessage("findNearestPointP: nearestPoint geom type: " + nearestPoint.geometry().wkbType(), tag="TOMs panel")
            return nearestPoint   # returns a point
        else:
            return None


    def findNearestPointL(self, searchPt, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        QgsMessageLog.logMessage("In findNearestPoint - lineLayer", tag="TOMs panel")
        searchRect = QgsRectangle(searchPt.x() - tolerance,
                                  searchPt.y() - tolerance,
                                  searchPt.x() + tolerance,
                                  searchPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        shortestDistance = float("inf")
        #nearestPoint = QgsFeature()

        # Loop through all features in the layer to find the closest feature
        for f in lineLayer.getFeatures(request):
            # Add any features that are found should be added to a list

            closestPtOnFeature = f.geometry().nearestPoint(QgsGeometry.fromPoint(searchPt))
            dist = f.geometry().distance(QgsGeometry.fromPoint(searchPt))
            if dist < shortestDistance:
                shortestDistance = dist
                closestPoint = closestPtOnFeature

        #QgsMessageLog.logMessage("In findNearestFeatureAt: shortestDistance: " + str(shortestDistance), tag="TOMs panel")

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            #QgsMessageLog.logMessage("findNearestPointL: nearestPoint geom type: " + str(nearestPoint.wkbType()), tag="TOMs panel")
            return closestPoint   # returns a geometry
        else:
            return None

    def findNearestLine(self, searchPt, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        QgsMessageLog.logMessage("In findNearestLine - lineLayer", tag="TOMs panel")
        searchRect = QgsRectangle(searchPt.x() - tolerance,
                                  searchPt.y() - tolerance,
                                  searchPt.x() + tolerance,
                                  searchPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        shortestDistance = float("inf")

        # Loop through all features in the layer to find the closest feature
        for f in lineLayer.getFeatures(request):
            # Add any features that are found should be added to a list

            #closestPtOnFeature = f.geometry().nearestPoint(QgsGeometry.fromPoint(searchPt))
            dist = f.geometry().distance(QgsGeometry.fromPoint(searchPt))
            if dist < shortestDistance:
                shortestDistance = dist
                closestLine = f

        QgsMessageLog.logMessage("In findNearestLine: shortestDistance: " + str(shortestDistance), tag="TOMs panel")

        if shortestDistance < float("inf"):

            """QgsMessageLog.logMessage("In findNearestLine: closestLine {}".format(closestLine.exportToWkt()),
                                     tag="TOMs panel")"""

            return closestLine   # returns a geometry
        else:
            return None


    def getStartPoint(self, restriction):
        #QgsMessageLog.logMessage("In getStartPoint", tag="TOMs panel")

        return restriction.geometry().vertexAt(0)


    def getEndPoint(self, restriction):
        #QgsMessageLog.logMessage("In getEndPoint", tag="TOMs panel")

        len = restriction.geometry().length()
        return restriction.geometry().vertexAt(len-1)


    def TraceRestriction(self, sourceLineLayer, snapLineLayer, tolerance):

        # For each vertex, check to see whether the next point is on the snapLineLayer.
        # If it is, include any additional vertices from the snapLineLayer

        QgsMessageLog.logMessage("In TraceRestriction", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        reply = QMessageBox.information(None, "Check",
                                        "TraceRestriction: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "TraceRestriction: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        lineTolerance = 0.01
        prevPointOnLine = False

        nearestVertexNrOnSnapLayerToCurrVertex = -2
        prevVertexNrOnSnapLayerToCurrVertex = -2
        nextVertexNrOnSnapLayerToCurrVertex = -2
        dist = float("inf")

        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            QgsMessageLog.logMessage("In TraceRestriction. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel")

            restGeom = currRestriction.geometry()
            nearestLine = self.findNearestLine(restGeom.asPolyline()[0], snapLineLayer, 0.01)

            if nearestLine:
            
                # Now, consider each vertex of the sourceLineLayer in turn

                QgsMessageLog.logMessage(
                    "In TraceRestriction. nearest line found. Considering " + str(len(restGeom.asPolyline())) + " points",
                    tag="TOMs panel")
                geomNearestLine = nearestLine.geometry()
                """QgsMessageLog.logMessage(
                    "In TraceRestriction: nearestLine1 {}".format(nearestLine.geometry().exportToWkt()),
                    tag="TOMs panel")"""
                prevPointOnLine = False

                for currVertexNr, currVertexPt in enumerate(restGeom.asPolyline()):

                    # Does this vertex lie on the line?
                    geomCurrVertex = QgsGeometry.fromPoint(currVertexPt)
                    distToLine = geomCurrVertex.shortestLine(geomNearestLine).length()

                    QgsMessageLog.logMessage(
                        "In TraceRestriction. " + str(
                            currRestriction.attribute("GeometryID")) + ": check for point on snapLineLayer at " + str(
                            currVertexNr),
                        tag="TOMs panel")

                    """QgsMessageLog.logMessage(
                        "Comparing: line  " + str(prevPtAgain.x()) + " " + str(prevPtAgain.y()) + " to " + str(
                            prevPt.x()) + " " + str(prevPt.y()) + ". Point is " + str(vertexPt.x()) + " " + str(vertexPt.y()) +
                            ". Dist is " + str(distToLine),
                        tag="TOMs panel")"""

                    if distToLine > lineTolerance:
                        currPointOnLine = False
                    else:

                        currPointOnLine = True

                        # Find nearest vertex
                        """nearestVertexOnSnapLayerToCurrVertex = geomNearestLine.closestVertex(
                            QgsPoint(currVertexPt.x(), currVertexPt.y()),
                            nearestVertexNrOnSnapLayerToCurrVertex,
                            prevVertexNrOnSnapLayerToCurrVertex,
                            nextVertexNrOnSnapLayerToCurrVertex,
                            dist)  # NB: QgsPointXY"""
                        nearestVertexOnSnapLayerToCurrVertex, \
                            nearestVertexNrOnSnapLayerToCurrVertex, \
                            prevVertexNrOnSnapLayerToCurrVertex, \
                            nextVertexNrOnSnapLayerToCurrVertex, \
                            dist = geomNearestLine.closestVertex(
                            QgsPoint(currVertexPt.x(), currVertexPt.y())
                            )  # NB: QgsPointXY

                        if prevPointOnLine is True:

                            # Trace ...

                            if nearestVertexOnSnapLayerToCurrVertex:

                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. Found point on Line - and prev point on line",
                                    tag="TOMs panel")

                                ptsOnNearestLine = nearestLine.geometry().asPolyline()

                                geomPrevVertex = QgsGeometry.fromPoint(prevVertexPt)
                                distTestA = geomPrevVertex.distance(QgsGeometry.fromPoint(QgsPoint(nearestVertexOnSnapLayerToCurrVertex.x(),
                                                                                           nearestVertexOnSnapLayerToCurrVertex.y())))
                                distTestB = geomPrevVertex.distance(QgsGeometry.fromPoint(QgsPoint(ptsOnNearestLine[prevVertexNrOnSnapLayerToCurrVertex].x(),
                                                                                                   ptsOnNearestLine[prevVertexNrOnSnapLayerToCurrVertex].y())))
                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. Starting distance tests",
                                    tag="TOMs panel")
                                # test to see direction of line
                                if distTestA > distTestB:
                                    traceLineAscending = True
                                    traceIncrement = 1
                                else:
                                    traceLineAscending = False
                                    traceIncrement = -1

                                # now check in relation to the nearestVertex
                                targetVertexForCurr = nearestVertexNrOnSnapLayerToCurrVertex

                                distTestC = geomPrevVertex.distance(QgsGeometry.fromPoint(currVertexPt))

                                if distTestC < distTestA:   # Need to change target to curr
                                    if traceLineAscending is True:
                                        targetVertexForCurr = prevVertexNrOnSnapLayerToCurrVertex
                                    else:
                                        targetVertexForCurr = nextVertexNrOnSnapLayerToCurrVertex

                                # Now consider the prev
                                targetVertexForPrev = nearestVertexNrOnSnapLayerToPrevVertex

                                distTestD = geomCurrVertex.distance(QgsGeometry.fromPoint(QgsPoint(nearestVertexOnSnapLayerToPrevVertex.x(),
                                                                                           nearestVertexOnSnapLayerToPrevVertex.y())))

                                if distTestC < distTestD:   # Need to change target
                                    if traceLineAscending is True:
                                        targetVertexForPrev = nextVertexNrOnSnapLayerToPrevVertex
                                    else:
                                        targetVertexForPrev = prevVertexNrOnSnapLayerToPrevVertex

                                QgsMessageLog.logMessage(
                                        "In TraceRestriction. Now adding vertices to restriction",
                                        tag="TOMs panel")
                                # Now have start/end vertices to add ... let's add
                                for i in range(targetVertexForPrev, targetVertexForCurr+1, traceIncrement):
                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction. Now adding vertices to restriction: vertex " + str(i) + " of " + str(len(ptsOnNearestLine)),
                                        tag="TOMs panel")

                                    restGeom.insertVertex(ptsOnNearestLine[i].x(),
                                                                 ptsOnNearestLine[i].y(),
                                                                 currVertexNr)

                            pass
                        pass

                        # Now set all the values for the curr to prev

                        QgsMessageLog.logMessage(
                            "In TraceRestriction. Now setting previous values",
                            tag="TOMs panel")

                        nearestVertexOnSnapLayerToPrevVertex = nearestVertexOnSnapLayerToCurrVertex
                        nearestVertexNrOnSnapLayerToPrevVertex = nearestVertexNrOnSnapLayerToCurrVertex
                        nextVertexNrOnSnapLayerToPrevVertex = nextVertexNrOnSnapLayerToCurrVertex
                        prevVertexNrOnSnapLayerToPrevVertex = prevVertexNrOnSnapLayerToCurrVertex

                    pass

                    QgsMessageLog.logMessage(
                        "In TraceRestriction. Point on line not found",
                        tag="TOMs panel")

                    prevPointOnLine = currPointOnLine
                    prevVertexPt = currVertexPt

        editCommitStatus = sourceLineLayer.commitChanges()

        #editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)


    def removeDuplicatePoints(self, sourceLineLayer, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        QgsMessageLog.logMessage("In removeDuplicatePoints", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "removeDuplicatePoints: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "removeDuplicatePoints: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Read through each restriction and compare each point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():

            restGeom = currRestriction.geometry()
            QgsMessageLog.logMessage(
                "In removeDuplicatePoints. Considering " + str(currRestriction.attribute("GeometryID")),
                tag="TOMs panel")

            line = currRestriction.geometry().asPolyline()
            #line = self.getLineForAz(currRestriction)
            for vertexNr in range(len(line)):
            #for vertexNr, vertexPt in enumerate(geom.asPolyline(), start=1):

                vertexPt = line[vertexNr]
                vertexDeleted = False

                if vertexNr > 0:

                    prevPt = line[vertexNr-1]

                    if abs(vertexPt.x() - prevPt.x()) < tolerance:
                        if abs(vertexPt.y() - prevPt.y()) < tolerance:
                            # have found duplicate
                            QgsMessageLog.logMessage(
                                "In removeDuplicatePoints. " + str(currRestriction.attribute("GeometryID")) + ": Duplicate at vertex " + str(vertexNr-1) + " / " + str(vertexNr),
                                tag="TOMs panel")
                            restGeom.deleteVertex(vertexNr)
                            vertexDeleted = True

                            QgsMessageLog.logMessage("Compared: curr  " + str(vertexPt.x()) + " " + str(vertexPt.y()) + " to " + str(
                                prevPt.x()) + " " + str(prevPt.y()),
                                tag="TOMs panel")

                if vertexNr > 1 and vertexDeleted is False:

                    # check whether or not this point is on a line between the last two
                    prevPtAgain = line[vertexNr-2]

                    geomVertex = QgsGeometry.fromPoint(vertexPt)
                    distToLine = geomVertex.shortestLine(QgsGeometry.fromPolyline([prevPt, prevPtAgain])).length()

                    """QgsMessageLog.logMessage(
                        "In removeDuplicatePoints. " + str(
                            currRestriction.attribute("GeometryID")) + ": check for point on line between " + str(
                            vertexNr - 1) + " / " + str(vertexNr),
                        tag="TOMs panel")
                    QgsMessageLog.logMessage(
                        "Comparing: line  " + str(prevPtAgain.x()) + " " + str(prevPtAgain.y()) + " to " + str(
                            prevPt.x()) + " " + str(prevPt.y()) + ". Point is " + str(vertexPt.x()) + " " + str(vertexPt.y()) +
                            ". Dist is " + str(distToLine),
                        tag="TOMs panel")"""

                    if distToLine < tolerance:

                        QgsMessageLog.logMessage(
                            "In removeDuplicatePoints. " + str(
                                currRestriction.attribute("GeometryID")) + ": Vertex " + str(vertexNr) + " is on line between previous two.",
                            tag="TOMs panel")
                        restGeom.deleteVertex(vertexNr)
                        vertexDeleted = True

                        QgsMessageLog.logMessage("Compared: curr  " + str(vertexPt.x()) + " " + str(vertexPt.y()) + " to " + str(
                            prevPt.x()) + " " + str(prevPt.y()),
                                                 tag="TOMs panel")

            pass

        editCommitStatus = sourceLineLayer.commitChanges()

        #editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

    def removeShortLines(self, sourceLineLayer, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        QgsMessageLog.logMessage("In removeShortLines", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "removeShortLines: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "removeShortLines: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Read through each restriction and compare each point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():

            QgsMessageLog.logMessage(
                "In removeShortLines. Considering " + str(currRestriction.attribute("GeometryID")),
                tag="TOMs panel")

            lenLine = currRestriction.geometry().length()

            if lenLine < tolerance:
                QgsMessageLog.logMessage(
                    "In removeShortLines. ------------ Removing " + str(currRestriction.attribute("GeometryID")),
                    tag="TOMs panel")
                sourceLineLayer.deleteFeature(currRestriction.id())

        editCommitStatus = sourceLineLayer.commitChanges()

        #editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "removeShortLines. Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)
