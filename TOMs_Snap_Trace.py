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

import os.path, math
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap
)

from qgis.PyQt.QtCore import (
    QObject, QTimer, pyqtSignal,
    QTranslator,
    QSettings,
    QCoreApplication,
    qVersion
)

from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    # QgsMapLayerRegistry,
    QgsMessageLog, QgsFeature, QgsGeometry, QgsGeometryUtils,
    QgsTransaction, QgsTransactionGroup,
    QgsProject,
    QgsApplication, QgsRectangle, QgsPoint, QgsWkbTypes, QgsPointXY,
    edit
)

from qgis.analysis import (
    QgsVectorLayerDirector, QgsNetworkDistanceStrategy, QgsGraphBuilder, QgsGraphAnalyzer
)


# Initialize Qt resources from file resources.py
from resources import *

# Import the code for the dialog
from TOMs_Snap_Trace_dialog import TOMsSnapTraceDialog
from TOMs.core.TOMsMessageLog import TOMsMessageLog
from TOMs.restrictionTypeUtilsClass import TOMsConfigFile

DUPLICATE_POINT_DISTANCE = 0.02
SMALL_ANGLE_RADIANS = 0.0001

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
        """locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TOMsSnapTrace_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)"""

        # Set up local logging
        loggingUtils = TOMsMessageLog()
        loggingUtils.setLogFile()

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

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            utils = SnapTraceUtils()
            # Set up variables to layers - maybe obtained from form ??

            indexBaysLayer = self.dlg.baysLayer.currentIndex()
            Bays = self.dlg.baysLayer.currentLayer()

            indexLinesLayer = self.dlg.linesLayer.currentIndex()
            Lines = self.dlg.linesLayer.currentLayer()

            """indexGNSSPointsLayer = self.dlg.gnssPointsLayer.currentIndex()
            GNSS_Points = self.dlg.gnssPointsLayer.currentLayer()"""

            indexsKerbLayer = self.dlg.kerbLayer.currentIndex()
            Kerbline = self.dlg.kerbLayer.currentLayer()

            if self.dlg.fld_Tolerance.text():
                tolerance = float(self.dlg.fld_Tolerance.text())
            else:
                tolerance = 0.5
            TOMsMessageLog.logMessage("Tolerance = " + str(tolerance),  level=Qgis.Info)

            removeShortLines = False
            removeDuplicatePoints = False
            #snapNodesToGNSS = False
            snapNodesTogether = False
            checkOverlapOption = False
            snapVerticesToKerb = False
            traceKerbline = False
            removePointsOutsideTolerance = False
            mergeGeometries = False
            restart_bays = False
            restart_lines = False

            if self.dlg.rb_removeShortLines.isChecked():
                removeShortLines = True

            if self.dlg.rb_removeDuplicatePoints.isChecked():
                removeDuplicatePoints = True

            """if self.dlg.rb_snapNodesToGNSS.isChecked():
                snapNodesToGNSS = True"""

            if self.dlg.rb_snapNodesTogether.isChecked():
                snapNodesTogether = True

            if self.dlg.rb_checkOverlaps.isChecked():
                checkOverlapOption = True

            if self.dlg.rb_snapVerticesToKerb.isChecked():
                snapVerticesToKerb = True

            if self.dlg.rb_traceKerbline.isChecked():
                traceKerbline = True

            if self.dlg.rb_mergeGeometries.isChecked():
                mergeGeometries = True

            """if self.dlg.rb_removePointsOutsideTolerance.isChecked():
                removePointsOutsideTolerance = True"""

            if self.dlg.cb_restart_bays.isChecked():
                restart_bays = True

            if self.dlg.cb_restart_lines.isChecked():
                restart_lines = True

            if Bays == Lines:
                listRestrictionLayers = [Bays]
            else:
                listRestrictionLayers = [Bays, Lines]

            if removeShortLines:

                TOMsMessageLog.logMessage("********** Removing short lines", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:

                    self.removeShortLines(currRestrictionLayer, tolerance)

            if removeDuplicatePoints:

                TOMsMessageLog.logMessage("********** Removing duplicate points", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:
                    utils.removeDuplicatePoints(currRestrictionLayer, DUPLICATE_POINT_DISTANCE)

            """if snapNodesToGNSS:

                TOMsMessageLog.logMessage("********** Snapping nodes to GNSS points", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:
                    utils.snapNodesP(currRestrictionLayer, GNSS_Points, tolerance)"""

            if snapNodesTogether:
                # Snap end points together ...  (Perhaps could use a double loop here ...)

                if Bays != Lines:
                    TOMsMessageLog.logMessage("********** Snapping lines to bays ...", level=Qgis.Warning)
                    utils.snapNodes(Lines, Bays, tolerance)

                TOMsMessageLog.logMessage("********** Snapping bays to bays ...", level=Qgis.Warning)
                utils.snapNodes(Bays, Bays, tolerance)

                if Bays != Lines:
                    TOMsMessageLog.logMessage("********** Snapping lines to lines ...", level=Qgis.Warning)
                    utils.snapNodes(Lines, Lines, tolerance)

            if checkOverlapOption:
                TOMsMessageLog.logMessage("********** checking overlaps ...", level=Qgis.Warning)
                for currRestrictionLayer in listRestrictionLayers:
                    utils.checkSelfOverlaps (currRestrictionLayer, tolerance)

            if snapVerticesToKerb:

                TOMsMessageLog.logMessage("********** Snapping vertices to kerb ...", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:
                    utils.snapVertices (currRestrictionLayer, Kerbline, tolerance)

            if traceKerbline:

                # Now trace ...
                # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

                TOMsMessageLog.logMessage("********** Tracing kerb ...", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:
                    utils.TraceRestriction3 (currRestrictionLayer, Kerbline, tolerance, restart_bays)

            # Set up all the layers - in init ...

            if removePointsOutsideTolerance:

                # Now trace ...
                # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

                TOMsMessageLog.logMessage("********** removePointsOutsideTolerance ...", level=Qgis.Warning)
                utils.removePointsOutsideTolerance (Bays, Kerbline, tolerance)

            if mergeGeometries:

                # Now trace ...
                # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

                TOMsMessageLog.logMessage("********** Tracing kerb ...", level=Qgis.Warning)

                for currRestrictionLayer in listRestrictionLayers:
                    utils.mergeGeometriesWithSameAttributes (currRestrictionLayer)

            # Set up all the layers - in init ...



class SnapTraceUtils():

    def __init__(self):
        pass

        """def snapNodesP(self, sourceLineLayer, snapPointLayer, tolerance):

        TOMsMessageLog.logMessage("In snapNodes", level=Qgis.Info)

        editStartStatus = sourceLineLayer.startEditing()

        reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)

        if editStartStatus is False:
            # save the active layer
            TOMsMessageLog.logMessage("Error: snapNodesP: Not able to start transaction on " + sourceLineLayer.name())
            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Snap node to nearest point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():
            #geom = feat.geometry()
            #attr = feat.attributes()

            if currRestriction.geometry() is None:
                continue

            ptsCurrRestriction = currRestriction.geometry().asPolyline()
            currPoint = self.getStartPoint(currRestriction)
            currVertex = 0
            #TOMsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), level=Qgis.Info)

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)   # returned as QgsFeature

            if nearestPoint:
                # Move the vertex
                TOMsMessageLog.logMessage("SnapNodes: Moving start point for " + str(currRestriction.attribute("GeometryID")), level=Qgis.Info)

                sourceLineLayer.moveVertex(nearestPoint.geometry().asPoint().x(), nearestPoint.geometry().asPoint().y(), currRestriction.id(), currVertex)
                # currRestriction.geometry().moveVertex(nearestPoint, currVertex)
                TOMsMessageLog.logMessage("In findNearestPointP: closestPoint {}".format(nearestPoint.geometry().exportToWkt()),
                                     level=Qgis.Info)

            currPoint = self.getEndPoint(currRestriction)

            nearestPoint = self.findNearestPointP(currPoint, snapPointLayer, tolerance)

            if nearestPoint:
                # Move the vertex
                TOMsMessageLog.logMessage("SnapNodes: Moving end point " + str(len(ptsCurrRestriction)-1) +
                                         " for " + str(currRestriction.attribute("GeometryID")), level=Qgis.Info)
                sourceLineLayer.moveVertex(nearestPoint.geometry().asPoint().x(),
                                                      nearestPoint.geometry().asPoint().y(), currRestriction.id(),
                                                    len(ptsCurrRestriction) - 1)

        editCommitStatus = sourceLineLayer.commitChanges()

        #reply = QMessageBox.information(None, "Check",
        #                                "SnapNodes: Status for commit to " + sourceLineLayer.name() + " is: " + str(
        #                                    editCommitStatus),
        #                                QMessageBox.Ok)

        if editCommitStatus is False:
            # save the active layer
            TOMsMessageLog.logMessage("Error: snapNodesP: Changes to " + sourceLineLayer.name() + " failed: " + str(
                sourceLineLayer.commitErrors()))
            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

        return
        """

    def snapNodes(self, sourceLineLayer, snapLineLayer, tolerance):

        TOMsMessageLog.logMessage("In snapNodes", level=Qgis.Info)

        editStartStatus = sourceLineLayer.startEditing()

        if editStartStatus is False:
            # save the active layer

            TOMsMessageLog.logMessage("Error: snapNodesL: Not able to start transaction on " + sourceLineLayer.name(), level=Qgis.Warning)
            reply = QMessageBox.information(None, "Error",
                                            "snapNodesL: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():

            TOMsMessageLog.logMessage("In snapNodes. Considering " + str(currRestriction.attribute("GeometryID")), level=Qgis.Info)
            currRestrictionGeom = currRestriction.geometry()
            currGeometryID = currRestriction.attribute("GeometryID")

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In snapNodes. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue

            if currRestrictionGeom.length() < tolerance:
                TOMsMessageLog.logMessage(
                    "In removeDuplicatePoints. LENGTH less than tolerance FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            newShape = self.checkRestrictionGeometryForSnappedNodes(currRestrictionGeom, snapLineLayer, tolerance, currGeometryID)

            if newShape:
                TOMsMessageLog.logMessage("In snapNodes. changes written ... ",
                                         level=Qgis.Info)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)

        #editCommitStatus = False

        editCommitStatus = sourceLineLayer.commitChanges()

        """reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for commit to " + sourceLineLayer.name() + " is: " + str(
                                            editCommitStatus),
                                        QMessageBox.Ok)"""

        if editCommitStatus is False:
            # save the active layer
            TOMsMessageLog.logMessage("Error: snapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                sourceLineLayer.commitErrors()), level=Qgis.Warning)
            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

        return

    def checkRestrictionGeometryForSnappedNodes(self, currRestrictionGeom, snapLineLayer, tolerance, currGeometryID=None):

        # Snap node to nearest point
        shapeChanged = False
        currRestrictionPtsList = currRestrictionGeom.asPolyline()
        startPoint = currRestrictionPtsList[0]
        endPoint = currRestrictionPtsList[len(currRestrictionPtsList)-1]
        #TOMsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), level=Qgis.Info)

        newStartNode, closestFeature = self.findNearestNodeOnLineLayer(startPoint, snapLineLayer, tolerance, [currGeometryID])
        if newStartNode:
            shapeChanged = True
            status = currRestrictionGeom.moveVertex(newStartNode, 0)

        newEndNode, closestFeature = self.findNearestNodeOnLineLayer(endPoint, snapLineLayer, tolerance, [currGeometryID])
        if newEndNode:
            shapeChanged = True
            status = currRestrictionGeom.moveVertex(newEndNode, (len(currRestrictionPtsList)-1))

        if shapeChanged:
            return currRestrictionGeom
        else:
            return None

    def snapVertices(self, sourceLineLayer, snapLineLayer, tolerance):
        # For each vertex within restriction, get nearest point on snapLineLayer ...
        TOMsMessageLog.logMessage("In snapVertices. Snapping " + sourceLineLayer.name() + " to " + snapLineLayer.name(), level=Qgis.Warning)
        TOMsMessageLog.logMessage("In snapVertices. " + str(sourceLineLayer.featureCount()) + " features in " + sourceLineLayer.name(), level=Qgis.Warning)

        editStartStatus = sourceLineLayer.startEditing()

        if editStartStatus is False:
            # save the active layer
            TOMsMessageLog.logMessage("Error: snapVertices: Not able to start transaction on " + sourceLineLayer.name(), level=Qgis.Warning)
            reply = QMessageBox.information(None, "Error",
                                            "Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():

            TOMsMessageLog.logMessage("In snapNodes. Considering " + str(currRestriction.attribute("GeometryID")),
                                     level=Qgis.Warning)
            currRestrictionGeom = currRestriction.geometry()

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In snapVertices. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            newShape = self.checkRestrictionGeometryForSnappedVertices(currRestrictionGeom, snapLineLayer, tolerance)

            if newShape:
                TOMsMessageLog.logMessage("In snapVertices. oldShape: ... {}".format(currRestrictionGeom.asWkt()),
                                         level=Qgis.Info)
                TOMsMessageLog.logMessage("In snapVertices. newShape: ... {}".format(newShape.asWkt()),
                                         level=Qgis.Info)
                TOMsMessageLog.logMessage("In snapVertices. changes written ... ",
                                         level=Qgis.Warning)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)

        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer
            TOMsMessageLog.logMessage("Error: snapVertices: Changes to " + sourceLineLayer.name() + " failed: " + str(
                sourceLineLayer.commitErrors()), level=Qgis.Warning)
            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

    def checkRestrictionGeometryForSnappedVertices(self, currRestrictionGeom, snapLineLayer, tolerance):

        # Snap vertices to nearest point on snapLineLayer
        TOMsMessageLog.logMessage("In checkRestrictionGeometryForSnappedVertices ... ", level=Qgis.Info)
        shapeChanged = False
        currRestrictionPtsList = currRestrictionGeom.asPolyline()
        #TOMsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), level=Qgis.Info)

        #newStartNode = self.findNearestNodeOnLine(startPoint, snapLineLayer, tolerance)

        for vertexNr, vertexPt in enumerate(currRestrictionPtsList):

            closestPoint = self.findNearestPointL(vertexPt, snapLineLayer, tolerance)
            #closestPoint, closestFeature = self.findNearestPointOnLineLayer(vertexPt, snapLineLayer, tolerance)  # TODO: Why was this included ??
            TOMsMessageLog.logMessage("In checkRestrictionGeometryForSnappedVertices. checking vertex ... ".format(vertexNr), level=Qgis.Info)
            if closestPoint:
                shapeChanged = True
                # TODO: what is the point is within tolerance of a node ?
                #TOMsMessageLog.logMessage("In checkRestrictionGeometryForSnappedVertices. vertex {} moved to {}".format(vertexNr, closestPoint.asWkt()), level=Qgis.Info)
                status = currRestrictionGeom.moveVertex(QgsPoint(closestPoint.asPoint()), vertexNr)
                TOMsMessageLog.logMessage("In checkRestrictionGeometryForSnappedVertices. vertex {} moved to {}: status: {}".format(vertexNr, closestPoint.asWkt(), status), level=Qgis.Info)

        if shapeChanged:
            return currRestrictionGeom
        else:
            return None


        """def findNearestPointP(self, searchPt, pointLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the given point layer
        # returns QgsPoint
        #TOMsMessageLog.logMessage("In findNearestPointP - pointLayer", level=Qgis.Info)

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

            #TOMsMessageLog.logMessage("findNearestPointP: nearestPoint geom type: " + str(f.geometry().wkbType()), level=Qgis.Info)
            dist = f.geometry().distance(QgsGeometry.fromPointXY(searchPt))
            if dist < shortestDistance:
                #TOMsMessageLog.logMessage("findNearestPointP: found 'nearer' point", level=Qgis.Info)
                shortestDistance = dist
                #nearestPoint = f.geometry()
                nearestPoint = f

        TOMsMessageLog.logMessage("In findNearestPointP: shortestDistance: " + str(shortestDistance), level=Qgis.Info)

        del request
        del searchRect

        if shortestDistance < float("inf"):

            TOMsMessageLog.logMessage("In findNearestPointP: closestPoint {}".format(nearestPoint.geometry().exportToWkt()),
                                     level=Qgis.Info)

            return nearestPoint   # returns a geometry
        else:
            return None
        """

    def findNearestPointL(self, searchPt, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        TOMsMessageLog.logMessage("In findNearestPointL. Checking lineLayer: " + lineLayer.name(), level=Qgis.Info)
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
            TOMsMessageLog.logMessage("In findNearestPointL: f.id: " + str(f.id()),
                                      level=Qgis.Info)
            closestPtOnFeature = f.geometry().nearestPoint(QgsGeometry.fromPointXY(searchPt))
            dist = f.geometry().distance(QgsGeometry.fromPointXY(searchPt))
            if dist < shortestDistance:
                shortestDistance = dist
                closestPoint = closestPtOnFeature

        TOMsMessageLog.logMessage("In findNearestPointL: shortestDistance: " + str(shortestDistance), level=Qgis.Info)

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            TOMsMessageLog.logMessage("findNearestPointL: nearest pt found ...".format(closestPoint.asWkt()), level=Qgis.Info)
            return closestPoint   # returns a geometry
        else:
            return None

    def findNearestPointOnLineLayer(self, searchPt, lineLayer, tolerance, geometryIDs=None):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        #TOMsMessageLog.logMessage("In findNearestPointL. Checking lineLayer: " + lineLayer.name(), level=Qgis.Info)
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
            if geometryIDs:
                #print ('***** currGeometryID: {}; GeometryID: {}'.format(currGeometryID, f.attribute("GeometryID")))
                try:
                    testGeometryID = f.attribute("GeometryID")
                except KeyError:
                    TOMsMessageLog.logMessage("In findNearestPointOnLineLayer. No GeometryID found on: " + lineLayer.name(), level=Qgis.Info)
                    break
                    # return None, None  # layer does not have "GeometryID" field, i.e., not restriction layer  TODO: Understand when then this used ...

                if testGeometryID in geometryIDs:
                    continue
            # Add any features that are found should be added to a list
            #print ('feature found: {}'.format(f.id()))
            closestPtOnFeature = f.geometry().nearestPoint(QgsGeometry.fromPointXY(searchPt))
            dist = f.geometry().distance(QgsGeometry.fromPointXY(searchPt))
            if dist < shortestDistance:
                shortestDistance = dist
                closestPoint = closestPtOnFeature
                closestFeature = f

        #TOMsMessageLog.logMessage("In findNearestPointL: shortestDistance: " + str(shortestDistance), level=Qgis.Info)

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            #TOMsMessageLog.logMessage("findNearestPointL: nearestPoint geom type: " + str(nearestPoint.wkbType()), level=Qgis.Info)
            return closestPoint, closestFeature   # returns a geometry
        else:
            return None, None

    def findNearestNodeOnLineLayer(self, searchPtXY, lineLayer, tolerance, geometryIDs=None):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint

        closestPoint, closestFeature = self.findNearestPointOnLineLayer(searchPtXY, lineLayer, tolerance, geometryIDs)

        if closestPoint:
            # check to see whether nodes are within tolerance
            searchPt = QgsPoint(searchPtXY)
            startPoint = self.getStartPoint(closestFeature)
            endPoint = self.getEndPoint(closestFeature)

            if searchPt.distance(startPoint) < tolerance:
                return startPoint, closestFeature
            elif searchPt.distance(endPoint) < tolerance:
                return endPoint, closestFeature

        return None, None

        """def findNearestPointL_2(self, searchPt, currRestriction, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        TOMsMessageLog.logMessage("In findNearestPointL_2. Checking lineLayer: " + lineLayer.name(), level=Qgis.Info)
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

            if f.id() != currRestriction.id():

                vertexCoord, vertex, prevVertex, nextVertex, distSquared = \
                    f.geometry().closestVertex(searchPt)
                dist = math.sqrt(distSquared)

                if dist < tolerance:

                    TOMsMessageLog.logMessage(
                        "In findNearestPointL_2. Found point: f.id: " + str(f.id()) + " curr_id: " + str(
                            currRestriction.id()),
                        level=Qgis.Info)

                    TOMsMessageLog.logMessage("In findNearestPointL_2. Setting distance ..." + str(dist), level=Qgis.Info)

                    if dist < shortestDistance:
                        shortestDistance = dist
                        closestPoint = f.geometry().vertexAt(vertex)

        #TOMsMessageLog.logMessage("In findNearestPointL: shortestDistance: " + str(shortestDistance), level=Qgis.Info)

        del request
        del searchRect

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            #TOMsMessageLog.logMessage("findNearestPointL: nearestPoint geom type: " + str(nearestPoint.wkbType()), level=Qgis.Info)
            return QgsGeometry.fromPointXY(closestPoint)   # returns a geometry
        else:
            return None


        def nearbyLineFeature(self, currFeatureGeom, searchLineLayer, tolerance):

        TOMsMessageLog.logMessage("In nearbyLineFeature - lineLayer", level=Qgis.Info)

        nearestLine = None

        for currVertexNr, currVertexPt in enumerate(currFeatureGeom.asPolyline()):

            nearestLine = self.findNearestLineLayer(currVertexPt, searchLineLayer, tolerance)
            if nearestLine:
                break

        return nearestLine
        """
    def findNearestLineLayer(self, searchPt, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        TOMsMessageLog.logMessage("In findNearestLine - lineLayer: " + lineLayer.name() + "; x:" + str(searchPt.x()), level=Qgis.Info)
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

            #closestPtOnFeature = f.geometry().nearestPoint(QgsGeometry.fromPointXY(searchPt))
            dist = f.geometry().distance(QgsGeometry.fromPointXY(searchPt))
            if dist < shortestDistance:
                shortestDistance = dist
                closestLine = f

        TOMsMessageLog.logMessage("In findNearestLine: shortestDistance: " + str(shortestDistance), level=Qgis.Info)

        del request
        del searchRect

        if shortestDistance < float("inf"):

            """TOMsMessageLog.logMessage("In findNearestLine: closestLine {}".format(closestLine.exportToWkt()),
                                     level=Qgis.Info)"""

            return closestLine   # returns a geometry
        else:
            return None


    def getStartPoint(self, restriction):
        #TOMsMessageLog.logMessage("In getStartPoint", level=Qgis.Info)
        return restriction.geometry().vertexAt(0)

    def getEndPoint(self, restriction):
        #TOMsMessageLog.logMessage("In getEndPoint", level=Qgis.Info)
        ptsCurrRestriction = restriction.geometry().asPolyline()
        return restriction.geometry().vertexAt(len(ptsCurrRestriction)-1)



        """def TraceRestriction2(self, sourceLineLayer, snapLineLayer, tolerance):

        TOMsMessageLog.logMessage("In TraceRestriction2", level=Qgis.Info)

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

            #TOMsMessageLog.logMessage("In TraceRestriction2. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel")

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In TraceRestriction2. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue

            nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

            # Check that this is not a circular feature, i.e., with the end points close to each other. If it is, it will cause some difficulties ...
            if self.circularFeature(currRestriction, tolerance):
                continue  # move to the next feature

            nearestLine = self.nearbyLineFeature(currRestrictionGeom, snapLineLayer, DUPLICATE_POINT_DISTANCE)

            if nearestLine:

                # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

                TOMsMessageLog.logMessage(
                    "In TraceRestriction2. nearest line found. Considering " + str(
                        len(currRestrictionGeom.asPolyline())) + " points",
                    level=Qgis.Info)
                nearestLineGeom = nearestLine.geometry()

                # initialise a new Geometry
                newGeometryCoordsList = []
                #newGeometryVertexNr = 0
                countDirectionAscending = None
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

                    # Insert Vertex A. NB: don't want to duplicate points
                    if countNewVertices > 1:
                        if not self.duplicatePoint(vertexA, newGeometryCoordsList[-1]):
                            TOMsMessageLog.logMessage("In TraceRestriction2: adding vertex " + str(currVertexNr), level=Qgis.Info)
                            newGeometryCoordsList.append(vertexA)
                            countNewVertices = countNewVertices + 1
                    else:  # first pass
                        newGeometryCoordsList.append(vertexA)
                        countNewVertices = countNewVertices + 1

                    # Does this segement lie on the Snapline? and if it lies within the buffer
                    # TODO: What happens if the trace line stops ... (perhaps check for the start/end)

                    if self.pointsOnLine(vertexA, vertexB, nearestLineGeom, DUPLICATE_POINT_DISTANCE) and \
                            self.lineInBuffer(vertexA, vertexB, nearestLineGeom, tolerance):

                        TOMsMessageLog.logMessage(
                            "In TraceRestriction2. " + str(
                                currRestriction.attribute(
                                    "GeometryID")) + ": considering segment between " + str(
                                currVertexNr) + " and " + str(currVertexNr + 1),
                            level=Qgis.Info)

                        # we have a line segement that needs to be traced. Set upi relevant variables

                        lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
                        lengthAB = lineAB_Geom.length()

                        distToA = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPointXY(vertexA))  #QgsGeometry of point ??
                        distToB = nearestLineGeom.lineLocatePoint (QgsGeometry.fromPointXY(vertexB))

                        # NB: countDirectionAscending only required once for each restriction

                        if countDirectionAscending == None:
                            # TODO: Getting errors with countDirection at start/end of line due (perhaps) to snapping issues. Would be better to check the countDirection over the length of the line??
                            countDirectionAscending = self.findCountDirection(distToA, distToB, lengthSnapLine, lengthAB)

                        TOMsMessageLog.logMessage("In TraceRestriction2: ******  countDirectionAscending " + str(countDirectionAscending), level=Qgis.Info)

                        # get closest vertices ...  NB: closestVertex returns point with nearest distance not necessarily "along the line", e.g., in a cul-de-sac

                        includeVertexAfterA, vertexNrAfterA, includeVertexAfterB, \
                            vertexNrAfterB = self.checkNeighbouringVertices(vertexA, vertexB, nearestLineGeom,
                                                                                countDirectionAscending, distToA, distToB)
                        # Now add relevant kerb vertices to restriction

                        currSnapLineVertex = nearestLineGeom.asPolyline()[vertexNrAfterA]
                        currSnapLineVertexNr = vertexNrAfterA

                        TOMsMessageLog.logMessage("In TraceRestriction2: ****** START nearestVertexAfterA " + str(vertexNrAfterA) + "; curr " + str(currSnapLineVertexNr) + " B: " + str(vertexNrAfterB), level=Qgis.Info)
                        #TOMsMessageLog.logMessage("In TraceRestriction2: ****** START vertexNrAfterA " + str(vertexNrAfterA) + " vertexNrAfterB: " + str(vertexNrAfterB), level=Qgis.Info)
                        TOMsMessageLog.logMessage("In TraceRestriction2: ******  includeVertexAfterA " + str(includeVertexAfterA) + "; includeVertexAfterB " + str(includeVertexAfterB), level=Qgis.Info)

                        if includeVertexAfterA:

                            TOMsMessageLog.logMessage(
                                "In TraceRestriction2: includeVertexAfterA: " + str(currSnapLineVertexNr) + " currSnapLineVertex: " + str(currSnapLineVertex.x()) + "," + str(currSnapLineVertex.y()), level=Qgis.Info)
                            TOMsMessageLog.logMessage("In TraceRestriction2: includeVertexAfterA: vertexA: " + str(vertexA.x()) + "," + str(vertexA.y()), level=Qgis.Info)

                            if not self.duplicatePoint(vertexA, currSnapLineVertex):
                                if not self.duplicatePoint(vertexB, currSnapLineVertex):
                                    newGeometryCoordsList.append(currSnapLineVertex)
                                    countNewVertices = countNewVertices + 1
                                    TOMsMessageLog.logMessage("In TraceRestriction2: ... including trace line vertex " + str(currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices), level=Qgis.Info)

                            status = self.insertVertexIntoRestriction(newGeometryCoordsList, curSnapLineVertex)
                            if status == True:
                                newGeometryVertexNr = newGeometryVertexNr + 1
                            else:
                                reply = QMessageBox.information(None, "Error",
                                                                "TraceRestriction2: Problem adding nearestVertexToA ",
                                                                QMessageBox.Ok)
                        stopped = False

                        if vertexNrAfterA == vertexNrAfterB:
                            stopped = True  # set stop flag for loop

                        while not stopped:

                            # find the next point (depending on direction of count and whether trace line index numbers pass 0)
                            if countDirectionAscending == True:
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

                            if currSnapLineVertexNr == vertexNrAfterB:
                                stopped = True  # set stop flag for loop
                                if includeVertexAfterB == False:
                                    break

                            # add the vertex - check first to see if it duplicates the previous point

                            if not self.duplicatePoint(newGeometryCoordsList[countNewVertices-1], currSnapLineVertex):
                                newGeometryCoordsList.append(currSnapLineVertex)
                                countNewVertices = countNewVertices + 1
                                TOMsMessageLog.logMessage("In TraceRestriction2: ... including trace line vertex " + str(currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices), level=Qgis.Info)
                                TOMsMessageLog.logMessage("In TraceRestriction2: vertexNrAfterA " + str(vertexNrAfterA) + "; curr " + str(currSnapLineVertexNr) + " vertexNrAfterB: " + str(vertexNrAfterB), level=Qgis.Info)

                            #if countNewVertices > 1000:
                                #break

                    # Insert Vertex B. This is the final point in the line - check for duplication ...
                    if countNewVertices > 1:
                        if self.duplicatePoint(vertexB, newGeometryCoordsList[-1]):
                            newGeometryCoordsList[-1] = vertexB
                            TOMsMessageLog.logMessage("In TraceRestriction2: overwriting last vertex ...", level=Qgis.Info)
                        else:
                            newGeometryCoordsList.append(vertexB)
                            countNewVertices = countNewVertices + 1
                    else:
                        newGeometryCoordsList.append(vertexB)
                        countNewVertices = countNewVertices + 1

                # Now replace the orginal geometry of the current restriction with the new geometry
                #currRestriction.setGeometry(QgsGeometry.fromPolyline(newGeometryCoordsList))

                newShape = QgsGeometry.fromPolyline(newGeometryCoordsList)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)
                TOMsMessageLog.logMessage("In TraceRestriction2. " + str(currRestriction.attribute("GeometryID")) +
                                         ": geometry changed ***. New nrVertices " + str(countNewVertices), level=Qgis.Info)
                TOMsMessageLog.logMessage("In TraceRestriction2: new geom: " + str(currRestriction.geometry().exportToWkt()),
                                         level=Qgis.Info)
                #TOMsMessageLog.logMessage(
                #   "In TraceRestriction2. " + str(currRestriction.attribute(
                #      "GeometryID")) + ": geometry changed ***. New nrVertices " + str(
                #     countNewVertices) + "; OrigLen: " + str(lengthAB) + " newLen: " + str(newShape.length()), level=Qgis.Info)

        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)
        """
    """
    ****** Approach whcih calculates shortest route between then snaps to that
    """

    def setupTrace(self, layer):
        reply = QMessageBox.information(None, "Information",
                                        "Setting up trace with " + layer.name(), QMessageBox.Ok)
        self.director = QgsVectorLayerDirector(layer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
        strategy = QgsNetworkDistanceStrategy()
        self.director.addStrategy(strategy)
        self.builder = QgsGraphBuilder(layer.crs())

    def getShortestPath(self, graphPtsList, layer):
        # taken from Qgis Py Cookbook
        #startPoint = self.ptList[0][0].asPoint()
        #endPoint = self.ptList[1][0].asPoint()
        """
        Difficult issue relates to situations where the restricition length is more than 50% of the relevant road casement length ...

        :param startPoint:
        :param endPoint:
        :param layer:
        :return:
        """

        self.director = QgsVectorLayerDirector(layer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
        strategy = QgsNetworkDistanceStrategy()
        self.director.addStrategy(strategy)
        self.builder = QgsGraphBuilder(layer.crs())

        TOMsMessageLog.logMessage("In getShortestPath: startPt: " + graphPtsList[0].asWkt(),
                                 level=Qgis.Info)
        tiedPoints = self.director.makeGraph(self.builder, graphPtsList)
        #TOMsMessageLog.logMessage("tiedPoints: {}".format(tiedPoints), level=Qgis.Info)
        tStart = tiedPoints[0]
        tStop = tiedPoints[-1]

        graph = self.builder.graph()
        idxStart = graph.findVertex(tStart)

        tree = QgsGraphAnalyzer.shortestTree(graph, idxStart, 0)

        idxStart = tree.findVertex(tStart)
        idxEnd = tree.findVertex(tStop)

        if idxEnd == -1:
            return None

        # Add last point
        route = [tree.vertex(idxEnd).point()]

        # Iterate the graph
        while idxEnd != idxStart:
            edgeIds = tree.vertex(idxEnd).incomingEdges()
            if len(edgeIds) == 0:
                break
            edge = tree.edge(edgeIds[0])
            route.insert(0, tree.vertex(edge.fromVertex()).point())
            idxEnd = edge.fromVertex()

        return route

    def TraceRestriction3(self, sourceLineLayer, snapLineLayer, tolerance, restart):

        TOMsMessageLog.logMessage("In TraceRestriction3", level=Qgis.Info)

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "TraceRestriction2: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "TraceRestriction2: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        # set up shortest path checker
        #self.setupTrace(snapLineLayer)


        featureCount = 0

        """ Loop through all features in layer - ordered by GeometryID - https://gis.stackexchange.com/questions/138769/is-it-possible-to-sort-the-features-by-an-attribute-programmatically """
        request = QgsFeatureRequest()
        clause = QgsFeatureRequest.OrderByClause('GeometryID', ascending=True)
        orderby = QgsFeatureRequest.OrderBy([clause])
        request.setOrderBy(orderby)

        restrictionIterator = sourceLineLayer.getFeatures(request)

        if restart == True:
            # prepare config file

            TOMsMessageLog.logMessage(
                "In TraceRestriction3. Restart requested ... ",
                level=Qgis.Warning)

            self.configFileFound = True
            self.TOMsConfigFileObject = TOMsConfigFile()
            self.TOMsConfigFileObject.TOMsConfigFileNotFound.connect(self.configFileNotFound)

            if self.configFileFound:
                self.TOMsConfigFileObject.initialiseTOMsConfigFile()
                featureCount = int(self.getRestartValue(sourceLineLayer.name())) - 1
                TOMsMessageLog.logMessage(
                    "In TraceRestriction3. Restarting at {} ... ".format(featureCount),
                    level=Qgis.Warning)

                i = 0
                while i < featureCount:
                    _ = next(restrictionIterator)
                    i = i + 1

        for currRestriction in restrictionIterator:  # TODO: Order by GeometryID

            featureCount = featureCount + 1
            
            TOMsMessageLog.logMessage("In TraceRestriction3. Considering {}: {}".format(featureCount, currRestriction.attribute("GeometryID")),
                                     level=Qgis.Warning)
            currRestrictionGeom = currRestriction.geometry()

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In TraceRestriction3. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            currRestrictionPtsList = currRestrictionGeom.asPolyline()
            startPoint = currRestrictionPtsList[0]
            endPoint = currRestrictionPtsList[len(currRestrictionPtsList) - 1]

            # check that start/end points are on the kerb
            """closestPointStart, closestFeatureStart = self.findNearestPointOnLineLayer(startPoint, snapLineLayer, tolerance)
            closestPointEnd, closestFeatureEnd = self.findNearestPointOnLineLayer(endPoint, snapLineLayer, tolerance)

            if not (closestPointStart and closestPointEnd):
                TOMsMessageLog.logMessage(
                    "In TraceRestriction3. *************** SKIPPING " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue"""

            graphPtsList = [startPoint, endPoint]
            if len(currRestrictionPtsList) > 2:
                midPoint = currRestrictionPtsList[int(len(currRestrictionPtsList)/2)]
                graphPtsList.insert(1, midPoint)
            route = self.getShortestPath(graphPtsList, snapLineLayer)
            if not route:
                TOMsMessageLog.logMessage(
                    "In TraceRestriction3. *************** SKIPPING " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            routeGeom = QgsGeometry.fromPolylineXY(route)

            if currRestrictionGeom.length() > routeGeom.length():
                # possibly situation where restriction passing over start/end of kerbline

                for vertexNr in range (0, len(currRestrictionPtsList)-1):
                    sectionRoute = self.getShortestPath([currRestrictionPtsList[vertexNr], currRestrictionPtsList[vertexNr+1]], snapLineLayer)
                    TOMsMessageLog.logMessage("In TraceRestriction3. vertex {}; sectionRoute = {}".format(vertexNr, sectionRoute),
                                      level=Qgis.Info)
                    # now join this section
                    if vertexNr == 0:
                        route = sectionRoute
                    else:
                        route.extend(sectionRoute[1:])  # don't repeat the first point

                routeGeom = QgsGeometry.fromPolylineXY(route)

            TOMsMessageLog.logMessage("In TraceRestriction3. route length = {}".format(routeGeom.length()),
                                      level=Qgis.Info)
            newShape = False

            if route:
                newShape = self.checkRestrictionGeometryForTracedVertices(currRestrictionGeom, routeGeom, tolerance)

            if newShape:
                TOMsMessageLog.logMessage("In TraceRestriction3. changes written ... ",
                                         level=Qgis.Warning)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)

            if featureCount%100 == 0:   # save changes after processing 100 features  TODO: can we do a restart based on the last saved item?

                TOMsMessageLog.logMessage("In TraceRestriction3. saving changes ... {}".format(featureCount),
                                          level=Qgis.Warning)
                editCommitStatus = sourceLineLayer.commitChanges()
                if editCommitStatus is False:
                    # save the active layer
                    reply = QMessageBox.information(None, "Error",
                                                    "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                        sourceLineLayer.commitErrors()), QMessageBox.Ok)
                # restart editing
                editStartStatus = sourceLineLayer.startEditing()
                if editStartStatus is False:
                    # save the active layer
                    reply = QMessageBox.information(None, "Error",
                                                    "TraceRestriction3: Not able to start transaction on " + sourceLineLayer.name(),
                                                    QMessageBox.Ok)
                    return

                # TODO: set restart value for layer

        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)
    def configFileNotFound(self):
        self.configFileFound = False
        QMessageBox.information(None, "ERROR", ("Config file not found ..."))

    def getRestartValue(self, layerName):
        configName = layerName + '.Restart'
        value = self.TOMsConfigFileObject.getTOMsConfigElement('TOMsSnapTrace', configName)
        if value:
            return value
        return 0


    """ ***** """
    def checkRestrictionGeometryForTracedVertices(self, currRestrictionGeom, routeGeom, tolerance):
        # Snap vertices to nearest point on snapLineLayer

        TOMsMessageLog.logMessage("In checkRestrictionGeometryForTracedVertices ...", level=Qgis.Info)

        currRestrictionPtsList = currRestrictionGeom.asPolyline()
        nrVerticesInCurrRestriction = len(currRestrictionPtsList)

        currVertexNr = 1
        shapeChanged = False
        vertexA = currRestrictionPtsList[0]
        newRestrictionPtsList = [vertexA]

        vertexAOnRoute = self.pointOnLine(vertexA, routeGeom)

        while currVertexNr <= (nrVerticesInCurrRestriction - 1):

            TOMsMessageLog.logMessage("In checkRestrictionGeometryForTracedVertices. Considering vertex {} ...".format(currVertexNr), level=Qgis.Info)
            vertexB = currRestrictionPtsList[currVertexNr]
            vertexBOnRoute = self.pointOnLine(vertexB, routeGeom)
            #print ('currVertexNr: {}; A: {}; B: {}'.format(currVertexNr, vertexA.asWkt(), vertexB.asWkt()))
            if vertexAOnRoute and vertexBOnRoute:
                # we have a trace situation
                #print('Tracing {} to {}'.format(currVertexNr-1, currVertexNr))
                TOMsMessageLog.logMessage(
                    "In checkRestrictionGeometryForTracedVertices. Both vertices on route. Tracing ...".format(currVertexNr),
                    level=Qgis.Info)
                routeSection = self.traceRouteGeom(vertexAOnRoute, vertexBOnRoute, routeGeom, tolerance)
                if routeSection:
                    TOMsMessageLog.logMessage("In checkRestrictionGeometryForTracedVertices. route section found ... ", level=Qgis.Info)
                    newRestrictionPtsList.extend(routeSection)
                    shapeChanged = True

            newRestrictionPtsList.append(vertexB)

            vertexA = vertexB
            vertexAOnRoute = vertexBOnRoute
            currVertexNr = currVertexNr + 1

        #print ('---------------')
        if shapeChanged:
            TOMsMessageLog.logMessage("In checkRestrictionGeometryForTracedVertices. shapeChanged ... ", level=Qgis.Info)
            return QgsGeometry.fromPolylineXY(newRestrictionPtsList)
        else:
            return None

    def traceRouteGeom(self, vertexA, vertexB, routeGeom, tolerance):

        # assumes that A abd B are on route

        distA = routeGeom.lineLocatePoint(QgsGeometry.fromPointXY(vertexA))
        distB = routeGeom.lineLocatePoint(QgsGeometry.fromPointXY(vertexB))
        lineAB_Geom = QgsGeometry.fromPolylineXY([vertexA, vertexB])

        # addRouteVerticesToRestrictionGeometry(vertexA, vertexB)
        routeSegmentPtsList = []
        shapeChanged = False

        vertex, vertexNr, prevVertexNr, nextVertexNr, distance = routeGeom.closestVertex(vertexA)
        distToVertexAOnRoute = routeGeom.distanceToVertex(vertexNr)

        if abs(distToVertexAOnRoute - distA) < DUPLICATE_POINT_DISTANCE:
            # same point
            currRouteVertexNr = nextVertexNr
        elif distToVertexAOnRoute < distA:
            currRouteVertexNr = nextVertexNr
        else:
            currRouteVertexNr = vertexNr

        distToNextRouteVertex = routeGeom.distanceToVertex(currRouteVertexNr)
        while distToNextRouteVertex < distB:
            # add point to newGeom
            if abs(distToNextRouteVertex - distB) < DUPLICATE_POINT_DISTANCE:
                break

            # check whether point is within tolerance
            currRouteVertex = QgsPointXY(routeGeom.vertexAt(currRouteVertexNr))
            distFromLineAB_ToCurrRouteVertex = lineAB_Geom.distance(QgsGeometry.fromPointXY(currRouteVertex))
            if distFromLineAB_ToCurrRouteVertex > tolerance:
                shapeChanged = False
                break

            routeSegmentPtsList.append(currRouteVertex)
            shapeChanged = True

            currRouteVertexNr = currRouteVertexNr + 1
            distToNextRouteVertex = routeGeom.distanceToVertex(currRouteVertexNr)

        if shapeChanged:
            return routeSegmentPtsList

        return None


    def pointOnLine(self, pt, line):
        ptGeom = QgsGeometry.fromPointXY(pt)
        nearestPt = line.nearestPoint(ptGeom)
        distance = nearestPt.distance(ptGeom)
        if nearestPt and distance < DUPLICATE_POINT_DISTANCE:
            return nearestPt.asPoint()
        return None

    def duplicatePoint(self, pointA, pointB):

        duplicate = False

        if pointA is None or pointB is None:
            duplicate = False
        elif math.sqrt((pointA.x() - pointB.x())**2 + ((pointA.y() - pointB.y())**2)) < DUPLICATE_POINT_DISTANCE:
            duplicate = True

        return duplicate

        """
        def circularFeature(self, currRestriction, lineTolerance):

        TOMsMessageLog.logMessage("In circularFeature", level=Qgis.Info)

        currRestrictionGeom = currRestriction.geometry()

        nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

        startVertex = currRestrictionGeom.asPolyline()[0]
        endVertex = currRestrictionGeom.asPolyline()[nrVerticesInCurrRestriction-1]

        dist = QgsGeometry.fromPointXY(startVertex).distance(QgsGeometry.fromPointXY(endVertex))

        if (dist <= lineTolerance):
            TOMsMessageLog.logMessage("In circularFeature: Circular feature found: " + currRestriction.attribute(
                        "GeometryID"), level=Qgis.Info)
            return True
        else:
            return False


        def pointsOnLine(self, vertexA, vertexB, nearestLineGeom, lineTolerance):

        TOMsMessageLog.logMessage("In pointsOnLine", level=Qgis.Info)

        vertexA_Geom = QgsGeometry.fromPointXY(vertexA)
        distNearestLineToVertexA = vertexA_Geom.shortestLine(nearestLineGeom).length()

        vertexB_Geom = QgsGeometry.fromPointXY(vertexB)
        distNearestLineToVertexB = vertexB_Geom.shortestLine(nearestLineGeom).length()

        if (distNearestLineToVertexA <= lineTolerance) and (distNearestLineToVertexB <= lineTolerance):
            return True
        else:
            return False


        def lineInBuffer(self, vertexA, vertexB, nearestLineGeom, bufferWidth):

        TOMsMessageLog.logMessage("In lineInBuffer", level=Qgis.Info)

        isWithin = False

        lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
        bufferGeom = nearestLineGeom.buffer(bufferWidth, 5)

        if lineAB_Geom.within(bufferGeom):
            isWithin = True

        return isWithin

        def findCountDirection(self, distToA, distToB, lengthSnapLine, lengthAB):

        TOMsMessageLog.logMessage("In findCountDirection", level=Qgis.Info)

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

        TOMsMessageLog.logMessage("In findCountDirection. Ascending: " + str(ascending) + " ShortestPath: " + str(shortestPath) + " lengthAB: " + str(lengthAB), level=Qgis.Info)

        # above processing assumes that want shortest distance. Need to check this is the case
        if lengthAB > (shortestPath * 1.1):
	        # Reverse order
            if ascending == True:
                return False
            if ascending == False:
                return True

        return ascending

        def checkNeighbouringVertices(self, vertexA, vertexB,
                                  nearestLineGeom, countDirectionAscending,
                                  distToA, distToB):

        # Now obtain the segement of the SnapLayer
        distSquared, closestPt, vertexNrAfterA = nearestLineGeom.closestSegmentWithContext(
            QgsPoint(vertexA.x(), vertexA.y()))
        distSquared, closestPt, vertexNrAfterB = nearestLineGeom.closestSegmentWithContext(
            QgsPoint(vertexB.x(), vertexB.y()))

        # TODO: Check that there are details returned ...

        distVertexAfterA = nearestLineGeom.lineLocatePoint(
            QgsGeometry.fromPointXY(nearestLineGeom.asPolyline()[vertexNrAfterA]))  # QgsPoint
        distVertexAfterB = nearestLineGeom.lineLocatePoint(
            QgsGeometry.fromPointXY(nearestLineGeom.asPolyline()[vertexNrAfterB]))
        # Work out whether or not nearest vertices need to be included …

        includeVertexAfterA = False
        includeVertexAfterB = False

        TOMsMessageLog.logMessage(
            "In checkNeighbouringVertices: --- vertexNrAfterA " + str(vertexNrAfterA) + "; vertexNrAfterB: " + str(vertexNrAfterB), level=Qgis.Info)
        TOMsMessageLog.logMessage(
            "In checkNeighbouringVertices: --- distVertexAfterA " + str(distVertexAfterA) + ": distToA " + str(distToA) + "; distVertexAfterB: " + str(distVertexAfterB) + ": distToB " + str(distToB), level=Qgis.Info)

        # standard case(s)
        if countDirectionAscending == True:  # ascending  NB: VertexAfterB always excluded (by definition)

            if distVertexAfterA < distToB and distVertexAfterA > 0.0:
                includeVertexAfterA = True

            # consider situation where line passes through vertex #0
            if (distToB < distToA):
                if distToB > 0.0:
                    includeVertexAfterA = True

        else:   # descending NB: VertexAfterA always excluded (by definition)

            if distVertexAfterB < distToA and distVertexAfterB > 0.0:
                includeVertexAfterB = True

            # consider situation where line passes through vertex #0
            if (distToA < distToB):
                if distToA > 0.0:
                    includeVertexAfterB = True

        # finally check for duplicate (or close) points
        if abs(distVertexAfterA - distToA) < DUPLICATE_POINT_DISTANCE:
            includeVertexAfterA = False
        if abs(distVertexAfterB - distToB) < DUPLICATE_POINT_DISTANCE:
            includeVertexAfterB = False

        return includeVertexAfterA, vertexNrAfterA, includeVertexAfterB, vertexNrAfterB
        """

    def removeDuplicatePoints(self, sourceLineLayer, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        TOMsMessageLog.logMessage("In removeDuplicatePoints", level=Qgis.Info)

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
        # Read through each restriction and compare successive points

        for currRestriction in sourceLineLayer.getFeatures():

            TOMsMessageLog.logMessage("In removeDuplicatePoints. Considering: " + str(currRestriction.attribute("GeometryID")), level=Qgis.Info)

            currRestrictionGeom = currRestriction.geometry()

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In removeDuplicatePoints. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            if currRestrictionGeom.length() < tolerance:
                TOMsMessageLog.logMessage(
                    "In removeDuplicatePoints. LENGTH less than tolerance FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            newShape = self.checkRestrictionGeometryForDuplicatePoints(currRestrictionGeom, tolerance)

            if newShape:
                TOMsMessageLog.logMessage("In removeDuplicatePoints. changes written ... ",
                                         level=Qgis.Info)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)

        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

    def checkRestrictionGeometryForDuplicatePoints(self, currRestrictionGeom, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        currRestrictionPtsList = currRestrictionGeom.asPolyline()
        nrVerticesInCurrRestriction = len(currRestrictionPtsList)

        currVertexNr = 1
        vertexA = currRestrictionPtsList[0]
        shapeChanged = False

        #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. nrVertices: " + str(nrVerticesInCurrRestriction), level=Qgis.Info)
        #print ('Nr vertices: {}'.format(nrVerticesInCurrRestriction))
        # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

        while currVertexNr < (nrVerticesInCurrRestriction):

            vertexB = currRestrictionPtsList[currVertexNr]

            #print (vertexA, vertexB, vertexC)
            if self.duplicatePoint(vertexA, vertexB):

                #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. found overlaps at " + str(currVertexNr),                                          level=Qgis.Info)
                #print ('In checkLineForSelfOverlap. found overlaps at {}'.format(currVertexNr))
                # do not want currVertex within new restriction
                currRestrictionPtsList.remove(currRestrictionPtsList[currVertexNr])
                nrVerticesInCurrRestriction = len(currRestrictionPtsList)
                shapeChanged = True
                #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. removing vertex" + str(currVertexNr),
                #                         level=Qgis.Info)
                #print ('In checkLineForSelfOverlap. removing vertex {}'.format(currVertexNr))
                if currVertexNr > 1:
                    currVertexNr = currVertexNr - 1

                vertexA = currRestrictionPtsList[currVertexNr - 1]

            else:

                vertexA = vertexB
                currVertexNr = currVertexNr + 1

        if shapeChanged:
            #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. changes written ... ",
            #                         level=Qgis.Info)
            #print ('In checkLineForSelfOverlap. changes written ...')
            newShape = QgsGeometry.fromPolylineXY(currRestrictionPtsList)
            return newShape

        return None


    def removeShortLines(self, sourceLineLayer, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        TOMsMessageLog.logMessage("In removeShortLines", level=Qgis.Info)

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

            TOMsMessageLog.logMessage(
                "In removeShortLines. Considering " + str(currRestriction.attribute("GeometryID")),
                level=Qgis.Info)

            lenLine = currRestriction.geometry().length()

            if lenLine < tolerance:
                TOMsMessageLog.logMessage(
                    "In removeShortLines. ------------ Removing " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                sourceLineLayer.deleteFeature(currRestriction.id())

        editCommitStatus = sourceLineLayer.commitChanges()
        #editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "removeShortLines. Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

    def checkSelfOverlaps(self, sourceLineLayer, tolerance):

        """ This is really to check whether or not there is a problem with the trace tool """

        TOMsMessageLog.logMessage("In checkSelfOverlaps " + sourceLineLayer.name(), level=Qgis.Warning)

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "checkSelfOverlaps: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "checkSelfOverlaps: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            TOMsMessageLog.logMessage("In checkSelfOverlaps. Considering: {}".format(currRestriction.attribute("GeometryID")), level=Qgis.Warning)

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In checkSelfOverlaps. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Warning)
                continue

            newShape = self.checkRestrictionGeometryForSelfOverlap(currRestrictionGeom, tolerance)

            if newShape:
                TOMsMessageLog.logMessage("In checkSelfOverlaps. changes written ... ",
                                         level=Qgis.Warning)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)


        TOMsMessageLog.logMessage("In checkOverlaps. Now finished layer ... ",
                                         level=Qgis.Warning)
        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    def checkSelfOverlaps_2(self, sourceLineLayer, snapLineLayer, tolerance):

        TOMsMessageLog.logMessage("In checkSelfOverlaps_2 ...", level=Qgis.Info)

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "checkSelfOverlaps_2: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "checkSelfOverlaps_2: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        # set up shortest path checker
        #self.setupTrace(snapLineLayer)

        for currRestriction in sourceLineLayer.getFeatures():

            TOMsMessageLog.logMessage("In checkSelfOverlaps_2. Considering " + str(currRestriction.attribute("GeometryID")),
                                     level=Qgis.Info)
            currRestrictionGeom = currRestriction.geometry()

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In checkSelfOverlaps_2. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue

            currRestrictionPtsList = currRestrictionGeom.asPolyline()

            # now check each line segement ... (make assumption that line has already been traced, i.e., matches kerbline)
            startPoint = currRestrictionPtsList[0]
            endPoint = currRestrictionPtsList[len(currRestrictionPtsList) - 1]

            # check that start/end points are on the kerb
            """closestPointStart, closestFeatureStart = self.findNearestPointOnLineLayer(startPoint, snapLineLayer, tolerance)
            closestPointEnd, closestFeatureEnd = self.findNearestPointOnLineLayer(endPoint, snapLineLayer, tolerance)

            if not (closestPointStart and closestPointEnd):
                TOMsMessageLog.logMessage(
                    "In TraceRestriction3. *************** SKIPPING " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue"""

            route = self.getShortestPath([startPoint, endPoint], snapLineLayer)
            if not route:
                TOMsMessageLog.logMessage(
                    "In checkSelfOverlaps_2. *************** SKIPPING " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue

            routeGeom = QgsGeometry.fromPolylineXY(route)
            newShape = False

            if route:
                newShape = self.checkRestrictionGeometryForTracedVertices(currRestrictionGeom, routeGeom, tolerance)

            if newShape:
                TOMsMessageLog.logMessage("In checkSelfOverlaps_2. changes written ... ",
                                         level=Qgis.Info)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)

        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)


    """ ***** """

    def checkRestrictionGeometryForSelfOverlap(self, currRestrictionGeom, tolerance):

        currRestrictionPtsList = currRestrictionGeom.asPolyline()
        nrVerticesInCurrRestriction = len(currRestrictionPtsList)

        vertexA = currRestrictionPtsList[0]
        vertexB = currRestrictionPtsList[1]

        newRestrictionPtsList = []
        newRestrictionPtsList.append(vertexA)
        newRestrictionPtsList.append(vertexB)

        currVertexNr = 1
        shapeChanged = False

        TOMsMessageLog.logMessage("In checkLineForSelfOverlap. nrVertices: {}".format(nrVerticesInCurrRestriction), level=Qgis.Warning)
        #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. nrVertices: " + str(nrVerticesInCurrRestriction), level=Qgis.Info)
        #print ('Nr vertices: {}'.format(nrVerticesInCurrRestriction))
        # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

        while currVertexNr < nrVerticesInCurrRestriction - 1:

            vertexC = currRestrictionPtsList[currVertexNr + 1]

            TOMsMessageLog.logMessage("In checkLineForSelfOverlap. considering pt {}".format(currVertexNr + 1),
                                      level=Qgis.Info)
            #print (vertexA, vertexB, vertexC)
            if self.isBetween(vertexA, vertexB, vertexC, tolerance):

                TOMsMessageLog.logMessage("In checkLineForSelfOverlap. found overlaps at {}".format(currVertexNr + 1), level=Qgis.Warning)
                #print ('In checkLineForSelfOverlap. found overlaps at {}'.format(currVertexNr))
                # do not want currVertex within new restriction
                #currRestrictionPtsList.remove(currRestrictionPtsList[currVertexNr + 1])
                #nrVerticesInCurrRestriction = len(currRestrictionPtsList)
                shapeChanged = True
                #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. removing vertex" + str(currVertexNr),
                #                         level=Qgis.Info)
                #print ('In checkLineForSelfOverlap. removing vertex {}'.format(currVertexNr))
                #if currVertexNr > 1:
                #    currVertexNr = currVertexNr - 1

                #vertexA = currRestrictionPtsList[currVertexNr - 1]

            else:

                newRestrictionPtsList.append(vertexC)
                vertexA = vertexB
                vertexB = vertexC

            currVertexNr = currVertexNr + 1

        if shapeChanged:
            TOMsMessageLog.logMessage("In checkLineForSelfOverlap. Shape changed. Nr of points now {} ... ".format(len(newRestrictionPtsList)), level=Qgis.Warning)
            #print ('In checkLineForSelfOverlap. changes written ...')
            newShape = QgsGeometry.fromPolylineXY(newRestrictionPtsList)
            return newShape

        return None

    def lineOverlaps(self, vertexA, vertexB, vertexC):

        prevDeltaX = vertexB.x() - vertexA.x()
        prevDeltaY = vertexB.y() - vertexA.y()
        currDeltaX = vertexC.x() - vertexB.x()
        currDeltaY = vertexC.y() - vertexB.y()

        dotProduct = currDeltaX * prevDeltaX + currDeltaY * prevDeltaY

        if dotProduct < 0:
            # candidate for overlap
            # calculate the angle between the vectors
            lenAB = math.sqrt(prevDeltaX**2 + prevDeltaY**2)
            lenBC = math.sqrt(currDeltaX**2 + currDeltaY**2)

            """if lenAB > 0 and lenBC > 0:
                angle = math.acos (dotProduct / (lenAB * lenBC))

                rem = angle % math.pi
                #print ('angle: {}; rem: {}'.format(angle, rem))

                if rem < SMALL_ANGLE_RADIANS:
                    return True"""

            lineAB_Geom = QgsGeometry.fromPolyline([QgsPoint(vertexA), QgsPoint(vertexB)])
            lineBC_Geom = QgsGeometry.fromPolyline([QgsPoint(vertexB), QgsPoint(vertexC)])

            intersectGeom = lineBC_Geom.intersection(lineAB_Geom)

            if intersectGeom.type() == QgsWkbTypes.LineGeometry:
                return True

            """overlap = lineBC_Geom.overlaps(lineAB_Geom.buffer(0.01, 5))
            if overlap:
                return True"""

        return False

    def isBetween(self, pointA, pointB, pointC, delta=None):
        # https://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
        # determines whether C lies on line A-B

        if delta is None:
            delta = 0.25

        # check to see whether or not point C lies within a buffer for A-B
        lineGeom_AB = QgsGeometry.fromPolylineXY([pointA, pointB])
        TOMsMessageLog.logMessage("In isBetween:  lineGeom ********: " + lineGeom_AB.asWkt(), level=Qgis.Info)
        buff = lineGeom_AB.buffer(delta, 0, QgsGeometry.CapFlat, QgsGeometry.JoinStyleBevel, 1.0)
        #TOMsMessageLog.logMessage("In isBetween:  buff ********: " + buff.asWkt(), level=Qgis.Info)

        if QgsGeometry.fromPointXY(pointC).intersects(buff):
            # candidate. Now check simple distances
            TOMsMessageLog.logMessage("In isBetween:  point is within buffer ...", level=Qgis.Info)
            lineGeom_AC = QgsGeometry.fromPolylineXY([pointA, pointC])
            lineGeom_BC = QgsGeometry.fromPolylineXY([pointB, pointC])
            distAB = lineGeom_AB.length()
            distAC = lineGeom_AC.length()
            distBC = lineGeom_BC.length()

            TOMsMessageLog.logMessage("In isBetween:  distances: {}; {}; {}".format(distAB, distAC, distBC), level=Qgis.Info)

            if abs(distAB - distAC) > (distBC - delta):
                return True

        return False

    def mergeGeometriesWithSameAttributes(self, sourceLineLayer):

        """ This is really to check whether or not there is a problem with the trace tool """

        checkFieldList = ["RestType", "GeomShapeID", "NrBays", "TimePeriodID", "PayTypeID",
                          "MaxStayID", "NoReturnID", "NoWaitingTimeID", "NoLoadingTimeID", "Unacceptability", "RoadName"]

        TOMsMessageLog.logMessage("In mergeGeometriesWithSameAttributes " + sourceLineLayer.name(), level=Qgis.Info)

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "mergeGeometriesWithSameAttributes: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "mergeGeometriesWithSameAttributes: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        # https://gis.stackexchange.com/questions/228267/merging-adjacent-lines-in-qgis

        already_processed = []
        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            TOMsMessageLog.logMessage("In mergeGeometriesWithSameAttributes. Considering: " + str(currRestriction.attribute("GeometryID")), level=Qgis.Info)

            currRestrictionGeom = currRestriction.geometry()

            if currRestrictionGeom.isEmpty():
                TOMsMessageLog.logMessage(
                    "In mergeGeometriesWithSameAttributes. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    level=Qgis.Info)
                continue

            currRestrictionAttributes = currRestriction.attributes()
            currGeometryID = currRestriction["GeometryID"]
            if currGeometryID not in already_processed:

                already_processed.append(currGeometryID)
                newShape = self.checkConnectedRestrictionsWithSameAttributes(currRestriction, sourceLineLayer, checkFieldList, already_processed)

                if newShape:
                    TOMsMessageLog.logMessage("In mergeGeometriesWithSameAttributes. changes written ... ",
                                             level=Qgis.Info)
                    sourceLineLayer.changeGeometry(currRestriction.id(), newShape)
                    already_processed.append(currGeometryID)

        TOMsMessageLog.logMessage("In mergeGeometriesWithSameAttributes. Now finished layer ... ",
                                         level=Qgis.Info)
        #editCommitStatus = False
        editCommitStatus = sourceLineLayer.commitChanges()

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    def checkConnectedRestrictionsWithSameAttributes(self, currRestriction, sourceLineLayer, checkFieldList, already_processed):

        stillLinesToCheck = True
        currRestrictionGeom = currRestriction.geometry()
        currGeometryID = currRestriction["GeometryID"]
        print ('******* checking: {}'.format(currGeometryID))
        TOMsMessageLog.logMessage('******* checking: {}'.format(currGeometryID),
                                 level=Qgis.Info)
        shapeChanged = False

        while stillLinesToCheck:

            currRestrictionPtsList = currRestrictionGeom.asPolyline()

            # get start/end points
            startPoint = currRestrictionPtsList[0]
            endPoint = currRestrictionPtsList[len(currRestrictionPtsList)-1]

            print ('start: {}; end: {}'.format(startPoint.asWkt(), endPoint.asWkt()))

            # find connected restrictions
            nodeList = [startPoint, endPoint]
            foundConnection = 0

            print ('already_processed: {}'.format(already_processed))
            print ('currRestrictionPtsList: {}'.format(currRestrictionPtsList))
            TOMsMessageLog.logMessage('already_processed: {}'.format(already_processed),
                                     level=Qgis.Info)
            for node in nodeList:

                node, feature = self.findNearestNodeOnLineLayer(node, sourceLineLayer,
                                                                            DUPLICATE_POINT_DISTANCE,
                                                                            already_processed)
                print ('******* considering: {}'.format(node))
                if node:
                    print ('*** node: {}'.format(feature["GeometryID"]))
                    TOMsMessageLog.logMessage('*** node: {}'.format(feature["GeometryID"]),
                                             level=Qgis.Info)
                    checkGeometryID = feature["GeometryID"]

                    if not(checkGeometryID in already_processed) and self.sameRestrictionAttributes(currRestriction, feature, checkFieldList):
                        print ('*** MERGING ***')
                        TOMsMessageLog.logMessage('*** MERGING ***',
                                                 level=Qgis.Info)
                        newShape = self.mergeRestrictionGeometries(feature.geometry(), currRestrictionGeom)
                        print (newShape)
                        shapeChanged = True

                        currRestrictionGeom = newShape # *******
                        foundConnection = foundConnection + 1

                        #with edit(sourceLineLayer):
                        sourceLineLayer.deleteFeature(feature.id())

                    already_processed.append(checkGeometryID)

            if foundConnection == 0:
                stillLinesToCheck = False

        if shapeChanged:
            #TOMsMessageLog.logMessage("In checkLineForSelfOverlap. changes written ... ",
            #                         level=Qgis.Info)
            #print ('In checkLineForSelfOverlap. changes written ...')
            newShape = QgsGeometry.fromPolylineXY(currRestrictionPtsList)
            return newShape

        return None

    def sameRestrictionAttributes(self, restrictionA, restrictionB, checkFieldList):
        # compare all relevant fields

        for checkField in checkFieldList:
            #print (checkField)
            try:
                #print ('{} -- A: {}; B: {}'.format(checkField, restrictionA[checkField], restrictionB[checkField]))
                test = restrictionA[checkField] == restrictionB[checkField]
            except Exception:
                return False

            if not test:
                return False

        return True

    def mergeRestrictionGeometries(self, restrictionA_Geom, restrictionB_Geom):

        # assume that nodes are snapped ??

        restrictionA_PtsList = restrictionA_Geom.asPolyline()
        startPointA = restrictionA_PtsList[0]
        endPointA = restrictionA_PtsList[len(restrictionA_PtsList)-1]

        restrictionB_PtsList = restrictionB_Geom.asPolyline()
        startPointB = restrictionB_PtsList[0]
        endPointB = restrictionB_PtsList[len(restrictionB_PtsList)-1]

        # work out orientation of lines normal is endA - startB

        if endPointA == startPointB:
            pass
        elif endPointA == endPointB:  # lines are going in opposite directions
            restrictionB_PtsList.reverse()
        elif startPointA == endPointB:  # lines are in same direction - just need to reverse order
            tmp = restrictionA_PtsList
            restrictionA_PtsList = restrictionB_PtsList
            restrictionB_PtsList = tmp
        elif startPointA == startPointB:  # lines in opposite directions and need to reverse order
            restrictionB_PtsList.reverse()
            tmp = restrictionA_PtsList
            restrictionA_PtsList = restrictionB_PtsList
            restrictionB_PtsList = tmp

        restrictionB_PtsList.pop(0)  # remove the first (duplicated) point of the second line
        restrictionA_PtsList.extend(restrictionB_PtsList)

        newShape = QgsGeometry.fromPolylineXY(restrictionA_PtsList)

        return newShape
