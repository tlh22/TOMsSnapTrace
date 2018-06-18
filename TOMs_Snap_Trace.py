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
            
            #tolerance =  float(self.dlg.fld_Tolerance.text())

            Bays = QgsMapLayerRegistry.instance().mapLayersByName("Bays")[0]
            Lines = QgsMapLayerRegistry.instance().mapLayersByName("Lines")[0]
            GNSS_Points = QgsMapLayerRegistry.instance().mapLayersByName("gnssPts_180117")[0]
            Kerbline = QgsMapLayerRegistry.instance().mapLayersByName("EDI_RoadCasement_Polyline")[0]

            if self.dlg.fld_Tolerance.text():
                tolerance = float(self.dlg.fld_Tolerance.text())
            else:
                tolerance = 0.5
            QgsMessageLog.logMessage("Tolerance = " + str(tolerance), tag="TOMs panel")

            # Snap nodes to GNSS points ...
            # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

            # Set up list of layers to be processed

            listRestrictionLayers = [Bays, Lines]

            """QgsMessageLog.logMessage("********** Removing short lines", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.removeShortLines(currRestrictionLayer, tolerance)

            QgsMessageLog.logMessage("********** Removing duplicate points", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.removeDuplicatePoints(currRestrictionLayer, tolerance)

            QgsMessageLog.logMessage("********** Snapping nodes to GNSS points", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.snapNodesP(currRestrictionLayer, GNSS_Points, tolerance)
                
            # Snap end points together ...  (Perhaps could use a double loop here ...)
            QgsMessageLog.logMessage("********** Snapping lines to bays ...", tag="TOMs panel")
            self.snapNodesL(Lines, Bays, tolerance)

            QgsMessageLog.logMessage("********** Snapping bays to bays ...", tag="TOMs panel")
            self.snapNodesL(Bays, Bays, tolerance)

            QgsMessageLog.logMessage("********** Snapping lines to lines ...", tag="TOMs panel")
            self.snapNodesL(Lines, Lines, tolerance)

            # Now snap vertices to the kerbline
            QgsMessageLog.logMessage("********** Snapping vertices to kerb ...", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.snapVertices (currRestrictionLayer, Kerbline, tolerance)"""
            
            # Now trace ...
            # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)
            QgsMessageLog.logMessage("********** Tracing kerb ...", tag="TOMs panel")

            for currRestrictionLayer in listRestrictionLayers:

                self.TraceRestriction2 (currRestrictionLayer, Kerbline, tolerance)
           
            # Set up all the layers - in init ...
 
    def snapNodesP(self, sourceLineLayer, snapPointLayer, tolerance):

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

            ptsCurrRestriction = currRestriction.geometry().asPolyline()
            currPoint = self.getStartPoint(currRestriction)
            currVertex = 0
            #QgsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), tag="TOMs panel")

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)   # returned as QgsFeature

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("SnapNodes: Moving start point for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")

                sourceLineLayer.moveVertex(nearestPoint.geometry().asPoint().x(), nearestPoint.geometry().asPoint().y(), currRestriction.id(), currVertex)
                # currRestriction.geometry().moveVertex(nearestPoint, currVertex)
                QgsMessageLog.logMessage("In findNearestPointP: closestPoint {}".format(nearestPoint.geometry().exportToWkt()),
                                     tag="TOMs panel")

            currPoint = self.getEndPoint(currRestriction)

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("SnapNodes: Moving end point " + str(len(ptsCurrRestriction)-1) +
                                         " for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")
                sourceLineLayer.moveVertex(nearestPoint.geometry().asPoint().x(),
                                                      nearestPoint.geometry().asPoint().y(), currRestriction.id(),
                                                    len(ptsCurrRestriction) - 1)

        editCommitStatus = sourceLineLayer.commitChanges()

        """reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for commit to " + sourceLineLayer.name() + " is: " + str(
                                            editCommitStatus),
                                        QMessageBox.Ok)"""

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

        return

    def snapNodesL(self, sourceLineLayer, snapLineLayer, tolerance):

        QgsMessageLog.logMessage("In snapNodesL", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "snapNodesL: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "snapNodesL: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Snap node to nearest point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():
            #geom = feat.geometry()
            #attr = feat.attributes()

            ptsCurrRestriction = currRestriction.geometry().asPolyline()
            currPoint = self.getStartPoint(currRestriction)
            currVertex = 0
            #QgsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), tag="TOMs panel")

            nearestPoint = self.findNearestPointL(currPoint, snapLineLayer, tolerance)   # returned as QgsFeature

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("snapNodesL: Moving start point for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")

                sourceLineLayer.moveVertex(nearestPoint.asPoint().x(), nearestPoint.asPoint().y(), currRestriction.id(), currVertex)
                # currRestriction.geometry().moveVertex(nearestPoint, currVertex)

                QgsMessageLog.logMessage("Moving vertex ( " + str(currVertex) + ") to " + str(
                    nearestPoint.asPoint().x()) + " " + str(nearestPoint.asPoint().y()),
                                     tag="TOMs panel")

            # Now consider the end point
            currPoint = self.getEndPoint(currRestriction)

            nearestPoint = self.findNearestPointL(currPoint, snapLineLayer, tolerance)

            if nearestPoint:
                # Move the vertex
                QgsMessageLog.logMessage("snapNodesL: Moving end point " + str(len(ptsCurrRestriction)-1) +
                                         " for " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")
                sourceLineLayer.moveVertex(nearestPoint.asPoint().x(),
                                                     nearestPoint.asPoint().y(), currRestriction.id(),
                                                    len(ptsCurrRestriction) - 1)
                QgsMessageLog.logMessage("Moving vertex ( " + str(len(ptsCurrRestriction) - 1) + ") to " + str(
                    nearestPoint.asPoint().x()) + " " + str(nearestPoint.asPoint().y()),
                                     tag="TOMs panel")

        editCommitStatus = sourceLineLayer.commitChanges()

        """reply = QMessageBox.information(None, "Check",
                                        "snapNodesL: Status for commit to " + sourceLineLayer.name() + " is: " + str(
                                            editCommitStatus),
                                        QMessageBox.Ok)"""

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
                    #moveStatus = geom.moveVertex(nearestPoint.asPoint().x(), nearestPoint.asPoint().y(), vertexNr)
                    moveStatus = sourceLineLayer.moveVertex(nearestPoint.asPoint().x(), nearestPoint.asPoint().y(), currRestriction.id(), vertexNr)
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

            #QgsMessageLog.logMessage("findNearestPointP: nearestPoint geom type: " + str(f.geometry().wkbType()), tag="TOMs panel")
            dist = f.geometry().distance(QgsGeometry.fromPoint(searchPt))
            if dist < shortestDistance:
                #QgsMessageLog.logMessage("findNearestPointP: found 'nearer' point", tag="TOMs panel")
                shortestDistance = dist
                #nearestPoint = f.geometry()
                nearestPoint = f

        QgsMessageLog.logMessage("In findNearestFeatureAt: shortestDistance: " + str(shortestDistance), tag="TOMs panel")


        if shortestDistance < float("inf"):

            QgsMessageLog.logMessage("In findNearestPointP: closestPoint {}".format(nearestPoint.geometry().exportToWkt()),
                                     tag="TOMs panel")

            return nearestPoint   # returns a geometry
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

    def nearbyLineFeature(self, currFeatureGeom, searchLineLayer, tolerance):

        QgsMessageLog.logMessage("In nearbyLineFeature - lineLayer", tag="TOMs panel")

        nearestLine = None

        for currVertexNr, currVertexPt in enumerate(currFeatureGeom.asPolyline()):

            nearestLine = self.findNearestLine(currVertexPt, searchLineLayer, tolerance)
            if nearestLine:
                break

        return nearestLine

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

        ptsCurrRestriction = restriction.geometry().asPolyline()
        return restriction.geometry().vertexAt(len(ptsCurrRestriction)-1)


    def TraceRestriction(self, sourceLineLayer, snapLineLayer, tolerance):

        # For each vertex, check to see whether the next point is on the snapLineLayer.
        # If it is, include any additional vertices from the snapLineLayer

        # another possible approach: https://gis.stackexchange.com/questions/263152/how-to-add-vertex-to-an-existing-polyline-in-qgis-using-python

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

            # TODO: Consider situation where the first point is not on the kerb

            if nearestLine:
            
                # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

                QgsMessageLog.logMessage(
                    "In TraceRestriction. nearest line found. Considering " + str(len(restGeom.asPolyline())) + " points",
                    tag="TOMs panel")
                geomNearestLine = nearestLine.geometry()
                """QgsMessageLog.logMessage(
                    "In TraceRestriction: nearestLine1 {}".format(nearestLine.geometry().exportToWkt()),
                    tag="TOMs panel")"""
                prevPointOnLine = False

                # initialise a new Geometry
                newGeometry = QgsGeometry()

                for currVertexNr, currVertexPt in enumerate(restGeom.asPolyline()):

                    """for seg_start, seg_end in pairs(line.asPolyline()):  # interesting approach
                        line_start = QgsPoint(seg_start)
                        line_end = QgsPoint(seg_end)"""

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
                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. nearestVertex: " + str(nearestVertexNrOnSnapLayerToCurrVertex) +
                                    "; prevVertex: " + str(
                                        prevVertexNrOnSnapLayerToCurrVertex) +
                                    "; nextVertex: " + str(
                                        nextVertexNrOnSnapLayerToCurrVertex),
                                    tag="TOMs panel")

                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. prevNearestVertex: " + str(nearestVertexOnSnapLayerToPrevVertex) +
                                    "; prevPrevVertex: " + str(
                                        nextVertexNrOnSnapLayerToPrevVertex) +
                                    "; nextPrevVertex: " + str(
                                        prevVertexNrOnSnapLayerToPrevVertex),
                                    tag="TOMs panel")

                                ptsOnNearestLine = nearestLine.geometry().asPolyline()

                                geomPrevVertex = QgsGeometry.fromPoint(prevVertexPt)
                                distTestA = geomPrevVertex.distance(QgsGeometry.fromPoint(QgsPoint(nearestVertexOnSnapLayerToCurrVertex.x(),
                                                                                           nearestVertexOnSnapLayerToCurrVertex.y())))
                                distTestB = geomPrevVertex.distance(QgsGeometry.fromPoint(QgsPoint(ptsOnNearestLine[prevVertexNrOnSnapLayerToCurrVertex].x(),
                                                                                                   ptsOnNearestLine[prevVertexNrOnSnapLayerToCurrVertex].y())))
                                # test to see direction of line
                                if distTestA > distTestB:
                                    traceLineAscending = True
                                    traceIncrement = 1
                                else:
                                    traceLineAscending = False
                                    traceIncrement = -1

                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. From distance tests, distTestA is : " + str(distTestA),
                                    tag="TOMs panel")
                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. From distance tests, distTestB is : " + str(distTestB),
                                    tag="TOMs panel")

                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. From distance tests, LineAscending is : " + str(traceLineAscending),
                                    tag="TOMs panel")

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
                                    "In TraceRestriction. From distance tests, distTestC is : " + str(distTestC),
                                    tag="TOMs panel")
                                QgsMessageLog.logMessage(
                                    "In TraceRestriction. From distance tests, distTestD is : " + str(distTestD),
                                    tag="TOMs panel")

                                QgsMessageLog.logMessage(
                                        "In TraceRestriction. Now adding vertices to restriction. Between "
                                        + str(targetVertexForPrev) + " and " + str(targetVertexForCurr),
                                        tag="TOMs panel")
                                # Now have start/end vertices to add ... let's add
                                # Now do some tests on the results to see if the points are outside the line

                                verticesAdded = False

                                diff = targetVertexForCurr - targetVertexForPrev

                                if traceLineAscending is True and diff < 0:
                                    verticesAdded = True

                                if traceLineAscending is False and diff > 0:
                                    verticesAdded = True

                                if diff == 0:
                                    # check to see if this point is on the line segment

                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction. diffCheck: " + str(
                                            ptsOnNearestLine[targetVertexForCurr].x()) +
                                        "; prevPrevVertex: " + str(
                                            ptsOnNearestLine[targetVertexForCurr].y()),
                                        tag="TOMs panel")

                                    distToLine = geomCurrVertex.shortestLine \
                                        (QgsGeometry.fromPoint(QgsPoint(ptsOnNearestLine[targetVertexForCurr].x(), \
                                                                        ptsOnNearestLine[targetVertexForCurr].y()))).length()
                                    if distToLine > lineTolerance:
                                        verticesAdded = True

                                if verticesAdded:
                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction. No vertices to add",
                                        tag="TOMs panel")

                                i = targetVertexForPrev
                                while verticesAdded is False:
                                    #for i in range(targetVertexForPrev, targetVertexForCurr+1, int(traceIncrement)):  # didn't take traceIncrement !!!

                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction. Now adding vertices to restriction: vertex " + str(i) + " of " + str(len(ptsOnNearestLine)),
                                        tag="TOMs panel")
                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction. Now adding vertices before: vertex " + str(currVertexNr),
                                    tag = "TOMs panel")

                                    """restGeom.insertVertex(ptsOnNearestLine[i].x(),
                                                                 ptsOnNearestLine[i].y(),
                                                                 currVertexNr)"""
                                    newGeometry.insertVertex(ptsOnNearestLine[i].x(),
                                                                 ptsOnNearestLine[i].y(), currRestriction.id(),
                                                                 currVertexNr)

                                    if i == targetVertexForCurr:
                                        verticesAdded = True
                                    i = i + traceIncrement
                                    currVertexNr = currVertexNr + 1   # Need to also increment this ...

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

                    # Need to generate a new geometry and replace ...

                    QgsMessageLog.logMessage(
                        "In TraceRestriction. Point on line not found",
                        tag="TOMs panel")

                    newGeometry.insertVertex(currVertexPt)

                    prevPointOnLine = currPointOnLine
                    prevVertexPt = currVertexPt

            # Now replace the orginal geometry of the current restriction with the new geometry
            currRestriction.setGeometry(newGeometry)
            #sourceLineLayer.changeGeometry(currRestriction.id(), newGeometry)

        #editCommitStatus = sourceLineLayer.commitChanges()

        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

    def TraceRestriction2(self, sourceLineLayer, snapLineLayer, tolerance):

        QgsMessageLog.logMessage("In TraceRestriction2", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        reply = QMessageBox.information(None, "Check",
                                        "TraceRestriction2: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "TraceRestriction2: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            QgsMessageLog.logMessage("In TraceRestriction2. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel")

            currRestrictionGeom = currRestriction.geometry()
            nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

            nearestLine = self.nearbyLineFeature(currRestrictionGeom, snapLineLayer, 0.01)

            if nearestLine:

                # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

                QgsMessageLog.logMessage(
                    "In TraceRestriction2. nearest line found. Considering " + str(
                        len(currRestrictionGeom.asPolyline())) + " points",
                    tag="TOMs panel")
                nearestLineGeom = nearestLine.geometry()

                # initialise a new Geometry
                newGeometryCoordsList = []
                #newGeometryVertexNr = 0
                countDirection = None
                nrVerticesInSnapLine = len(nearestLineGeom.asPolyline())
                lengthSnapLine = nearestLineGeom.length()
                countNewVertices = 0

                for currVertexNr, currVertexPt in enumerate(currRestrictionGeom.asPolyline()):

                    # Check we haven't reached the last vertex
                    if currVertexNr == (nrVerticesInCurrRestriction - 1):
                        break

                    # Now consider line segment
                    vertexA = currVertexPt
                    vertexB = currRestrictionGeom.asPolyline()[currVertexNr+1]

                    # Insert Vertex A. NB: don't want to duplicate points so only add end point as last action
                    newGeometryCoordsList.append(vertexA)
                    countNewVertices = countNewVertices + 1

                    # Does this segement lie on the Snapline?

                    if self.pointsOnLine(vertexA, vertexB, nearestLineGeom, 0.01):

                        QgsMessageLog.logMessage(
                            "In TraceRestriction2. " + str(
                                currRestriction.attribute(
                                    "GeometryID")) + ": considering segment between " + str(
                                currVertexNr) + " and " + str(currVertexNr + 1),
                            tag="TOMs panel")

                        # we have a line segement that needs to be traced. Set upi relevant variables

                        lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
                        lengthAB = lineAB_Geom.length()

                        distToA = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPoint(vertexA))  #QgsGeometry of point ??
                        distToB = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPoint(vertexB))

                        # NB: countDirection only required once for each restriction

                        if countDirection == None:
                            countDirection = self.findCountDirection(distToA, distToB, lengthSnapLine, lengthAB)

                        # get closest vertices ...

                        nearestVertexToA, nearestVertexNrToA, prevVertexNrToA, \
                            nextVertexNrToA, dist = nearestLineGeom.closestVertex(QgsPoint(vertexA.x(), vertexA.y()))  # NB: QgsPointXY
                        nearestVertexToB, nearestVertexNrToB, prevVertexNrToB, \
                            nextVertexNrToB, dist = nearestLineGeom.closestVertex(QgsPoint(vertexB.x(), vertexB.y()))  # NB: QgsPointXY

                        distClosestVertexToA = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPoint(nearestVertexToA))  # QgsPoint
                        distClosestVertexToB = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPoint(nearestVertexToB))

                        # Work out whether or not nearest vertices need to be included …

                        includeClosestVertexToA = False
                        includeClosestVertexToB = False

                        if countDirection == True:  # ascending

                            if distClosestVertexToA > distToA:
                                includeClosestVertexToA = True
                            if distClosestVertexToB < distToB:
                                if nearestVertexNrToA <> nearestVertexNrToB:
                                    includeClosestVertexToB = True
                        else:
                            if distClosestVertexToA < distToA:
                                includeClosestVertexToA = True
                            if distClosestVertexToB > distToB:
                                if nearestVertexNrToA <> nearestVertexNrToB:
                                    includeClosestVertexToB = True

                        # Now add relevant kerb vertices to restriction

                        currSnapLineVertex = nearestVertexToA
                        currSnapLineVertexNr = nearestVertexNrToA

                        if includeClosestVertexToA:
                            newGeometryCoordsList.append(nearestVertexToA)
                            countNewVertices = countNewVertices + 1

                            """status = self.insertVertexIntoRestriction(newGeometryCoordsList, curSnapLineVertex)
                            if status == True:
                                newGeometryVertexNr = newGeometryVertexNr + 1
                            else:
                                reply = QMessageBox.information(None, "Error",
                                                                "TraceRestriction2: Problem adding nearestVertexToA ",
                                                                QMessageBox.Ok)"""

                        stopped = False

                        while not stopped:

                            if countDirection == True:
                                currSnapLineVertexNr = currSnapLineVertexNr + 1
                                if currSnapLineVertexNr == nrVerticesInSnapLine:
                                    # currently at end of line and need to continue from start
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[0]
                                    currSnapLineVertexNr = 0
                                else:
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[currSnapLineVertexNr]

                            else:
                                currSnapLineVertexNr = currSnapLineVertexNr - 1
                                if currSnapLineVertexNr < 0:
                                    # currently at end of line and need to continue from start
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[nrVerticesInSnapLine-1]
                                    currSnapLineVertexNr = nrVerticesInSnapLine-1
                                else:
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[currSnapLineVertexNr]

                            if currSnapLineVertexNr == nearestVertexNrToB:
                                stopped = True  # set stop flag for loop
                                if includeClosestVertexToB == False:
                                    break

                            # add the vertex

                            newGeometryCoordsList.append(currSnapLineVertex)
                            countNewVertices = countNewVertices + 1
                            QgsMessageLog.logMessage("In TraceRestriction2: countNewVertices " + str(countNewVertices), tag="TOMs panel")
                            QgsMessageLog.logMessage("In TraceRestriction2: countNewVertices " + str(nearestVertexNrToA) + "; curr " + str(currSnapLineVertexNr) + " B: " + str(nearestVertexNrToB), tag="TOMs panel")

                            if countNewVertices > 1000:
                                break

                # Insert Vertex B. This is the final point in the line
                newGeometryCoordsList.append(vertexB)
                countNewVertices = countNewVertices + 1

                # Now replace the orginal geometry of the current restriction with the new geometry
                #currRestriction.setGeometry(QgsGeometry.fromPolyline(newGeometryCoordsList))
                newGeometryCoordsListV2 = []
                lineString = QgsLineStringV2()
                for x in newGeometryCoordsList:
                    newGeometryCoordsListV2.append(QgsPointV2(x))

                lineString.setPoints(newGeometryCoordsListV2)

                currRestriction.setGeometry(QgsGeometry(lineString))

                #sourceLineLayer.changeGeometry(currRestriction.id(), QgsGeometry.fromPolyline(newGeometryCoordsList))

                QgsMessageLog.logMessage(
                    "In TraceRestriction2. " + str(currRestriction.attribute(
                            "GeometryID")) + ": geometry changed. New nrVertices " + str(
                        countNewVertices), tag="TOMs panel")

                # sourceLineLayer.changeGeometry(currRestriction.id(), newGeometry)

        # editCommitStatus = sourceLineLayer.commitChanges()

        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    def pointsOnLine(self, vertexA, vertexB, nearestLineGeom, lineTolerance):

        QgsMessageLog.logMessage("In pointsOnLine", tag="TOMs panel")

        vertexA_Geom = QgsGeometry.fromPoint(vertexA)
        distNearestLineToVertexA = vertexA_Geom.shortestLine(nearestLineGeom).length()

        vertexB_Geom = QgsGeometry.fromPoint(vertexB)
        distNearestLineToVertexB = vertexB_Geom.shortestLine(nearestLineGeom).length()

        if (distNearestLineToVertexA <= lineTolerance) and (distNearestLineToVertexB <= lineTolerance):
            return True
        else:
            return False

    def findCountDirection(self, distToA, distToB, lengthSnapLine, lengthAB):

        QgsMessageLog.logMessage("In findCountDirection", tag="TOMs panel")

        # function to determine count direction for moving along lineAB in respect to the numbering on SnapLine

        if distToA > distToB:
            Opt1 = distToA - distToB
            Opt2 = lengthSnapLine - distToA + distToB
        else:
            Opt1 = distToB - distToA
            Opt2 = lengthSnapLine - distToB + distToA

        # Now work our out the sequencing assuming shortest distance is required
        if Opt1 < Opt2:
            # Normal sequencing … i.e., doesn’t pass 0
            shortestPath = Opt1
            if distToA < distToB:
                ascending = True
            else:
                ascending = False
        else:
            # sequence passes 0
            shortestPath = Opt2
            if distToA > distToB:
                ascending = True
            else:
                ascending = False

        QgsMessageLog.logMessage("In findCountDirection. Ascending: " + str(ascending) + " ShortestPath: " + str(shortestPath) + " lengthAB: " + str(lengthAB), tag="TOMs panel")

        # above processing assumes that want shortest distance. Need to check this is the case
        if lengthAB > (shortestPath + 10):
	        # Reverse order
            if ascending == True:
                return False
            if ascending == False:
                return True

        return ascending

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
                            #restGeom.deleteVertex(vertexNr)
                            #restGeom.deleteVertex(vertexNr)
                            sourceLineLayer.deleteVertex(currRestriction.id(), vertexNr)
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
                        #restGeom.deleteVertex(vertexNr)
                        sourceLineLayer.deleteVertex(currRestriction.id(), vertexNr)
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

