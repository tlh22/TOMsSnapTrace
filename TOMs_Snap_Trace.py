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
import os.path, math

"""
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
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    # QgsMapLayerRegistry,
    QgsMessageLog, QgsFeature, QgsGeometry,
    QgsTransaction, QgsTransactionGroup,
    QgsProject,
    QgsApplication
)
"""
DUPLICATE_POINT_DISTANCE = 0.02

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

        """layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                self.dlg.baysLayer.addItem( layer.name(), layer )
                self.dlg.linesLayer.addItem( layer.name(), layer )
                self.dlg.gnssPointsLayer.addItem( layer.name(), layer )
                self.dlg.kerbLayer.addItem(layer.name(), layer)
                # self.dlg.layerValues.addItem( layer.name(), layer )"""


        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            # Set up variables to layers - maybe obtained from form ??

            indexBaysLayer = self.dlg.baysLayer.currentIndex()
            Bays = self.dlg.baysLayer.currentLayer()

            indexLinesLayer = self.dlg.linesLayer.currentIndex()
            Lines = self.dlg.linesLayer.currentLayer()

            indexGNSSPointsLayer = self.dlg.gnssPointsLayer.currentIndex()
            GNSS_Points = self.dlg.gnssPointsLayer.currentLayer()

            indexsKerbLayer = self.dlg.kerbLayer.currentIndex()
            Kerbline = self.dlg.kerbLayer.currentLayer()

            #tolerance =  float(self.dlg.fld_Tolerance.text())

            """Bays = QgsMapLayerRegistry.instance().mapLayersByName("Bays")[0]
            Lines = QgsMapLayerRegistry.instance().mapLayersByName("Lines")[0]
            GNSS_Points = QgsMapLayerRegistry.instance().mapLayersByName("gnssPts_180117")[0]
            Kerbline = QgsMapLayerRegistry.instance().mapLayersByName("EDI_RoadCasement_Polyline")[0]"""

            if self.dlg.fld_Tolerance.text():
                tolerance = float(self.dlg.fld_Tolerance.text())
            else:
                tolerance = 0.5
            QgsMessageLog.logMessage("Tolerance = " + str(tolerance), tag="TOMs panel")

            removeShortLines = False
            removeDuplicatePoints = False
            snapNodesToGNSS = False
            snapNodesTogether = False
            checkOverlapOption = False
            snapVerticesToKerb = False
            traceKerbline = False
            removePointsOutsideTolerance = False

            if self.dlg.rb_removeShortLines.isChecked():
                removeShortLines = True

            if self.dlg.rb_removeDuplicatePoints.isChecked():
                removeDuplicatePoints = True

            if self.dlg.rb_snapNodesToGNSS.isChecked():
                snapNodesToGNSS = True

            if self.dlg.rb_snapNodesTogether.isChecked():
                snapNodesTogether = True

            if self.dlg.rb_checkOverlaps.isChecked():
                checkOverlapOption = True

            if self.dlg.rb_snapVerticesToKerb.isChecked():
                snapVerticesToKerb = True

            if self.dlg.rb_traceKerbline.isChecked():
                traceKerbline = True

            """if self.dlg.rb_removePointsOutsideTolerance.isChecked():
                removePointsOutsideTolerance = True"""

            # Snap nodes to GNSS points ...
            # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

            # Set up list of layers to be processed

            if Bays == Lines:
                listRestrictionLayers = [Bays]
            else:
                listRestrictionLayers = [Bays, Lines]

            if removeShortLines:

                QgsMessageLog.logMessage("********** Removing short lines", tag="TOMs panel")

                """for currRestrictionLayer in listRestrictionLayers:

                    self.removeShortLines(currRestrictionLayer, tolerance)"""

            if removeDuplicatePoints:

                QgsMessageLog.logMessage("********** Removing duplicate points", tag="TOMs panel")

                for currRestrictionLayer in listRestrictionLayers:

                    self.removeDuplicatePoints(currRestrictionLayer, DUPLICATE_POINT_DISTANCE)

            if snapNodesToGNSS:

                QgsMessageLog.logMessage("********** Snapping nodes to GNSS points", tag="TOMs panel")

                for currRestrictionLayer in listRestrictionLayers:

                    self.snapNodesP(currRestrictionLayer, GNSS_Points, tolerance)

            if snapNodesTogether:
                # Snap end points together ...  (Perhaps could use a double loop here ...)

                if Bays != Lines:
                    QgsMessageLog.logMessage("********** Snapping lines to bays ...", tag="TOMs panel")
                    self.snapNodesL(Lines, Bays, tolerance)

                QgsMessageLog.logMessage("********** Snapping bays to bays ...", tag="TOMs panel")
                self.snapNodesL(Bays, Bays, tolerance)

                if Bays != Lines:
                    QgsMessageLog.logMessage("********** Snapping lines to lines ...", tag="TOMs panel")
                    self.snapNodesL(Lines, Lines, tolerance)

            if checkOverlapOption:
                QgsMessageLog.logMessage("********** checking overlaps ...", tag="TOMs panel")
                for currRestrictionLayer in listRestrictionLayers:
                    self.checkOverlaps (currRestrictionLayer, tolerance)

            if snapVerticesToKerb:

                QgsMessageLog.logMessage("********** Snapping vertices to kerb ...", tag="TOMs panel")

                for currRestrictionLayer in listRestrictionLayers:

                    self.snapVertices (currRestrictionLayer, Kerbline, tolerance)

            if traceKerbline:

                # Now trace ...
                # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

                QgsMessageLog.logMessage("********** Tracing kerb ...", tag="TOMs panel")

                for currRestrictionLayer in listRestrictionLayers:

                    self.TraceRestriction2 (currRestrictionLayer, Kerbline, tolerance)

            # Set up all the layers - in init ...

            if removePointsOutsideTolerance:

                # Now trace ...
                # For each restriction layer ? (what about signs and polygons ?? (Maybe only lines and bays at this point)

                QgsMessageLog.logMessage("********** removePointsOutsideTolerance ...", tag="TOMs panel")

                self.removePointsOutsideTolerance (Bays, Kerbline, tolerance)




    def snapNodesP(self, sourceLineLayer, snapPointLayer, tolerance):

        QgsMessageLog.logMessage("In snapNodes", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        reply = QMessageBox.information(None, "Check",
                                        "SnapNodes: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)

        if editStartStatus is False:
            # save the active layer
            QgsMessageLog.logMessage("Error: snapNodesP: Not able to start transaction on " + sourceLineLayer.name())
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
            QgsMessageLog.logMessage("Error: snapNodesP: Changes to " + sourceLineLayer.name() + " failed: " + str(
                sourceLineLayer.commitErrors()))
            reply = QMessageBox.information(None, "Error",
                                            "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)

        return

    def snapNodesL(self, sourceLineLayer, snapLineLayer, tolerance):

        QgsMessageLog.logMessage("In snapNodesL", tag="TOMs panel")

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():
            #geom = feat.geometry()
            #attr = feat.attributes()

            editStartStatus = sourceLineLayer.startEditing()

            """reply = QMessageBox.information(None, "Check",
                                            "snapNodesL: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                                editStartStatus),
                                            QMessageBox.Ok)"""

            if editStartStatus is False:
                # save the active layer

                QgsMessageLog.logMessage("Error: snapNodesL: Not able to start transaction on " + sourceLineLayer.name())
                reply = QMessageBox.information(None, "Error",
                                                "snapNodesL: Not able to start transaction on " + sourceLineLayer.name(),
                                                QMessageBox.Ok)
                return
            # Snap node to nearest point

            if currRestriction.geometry() is None:
                continue

            QgsMessageLog.logMessage("In snapNodesL. Considering " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")
            ptsCurrRestriction = currRestriction.geometry().asPolyline()
            currPoint = self.getStartPoint(currRestriction)
            currVertex = 0
            #QgsMessageLog.logMessage("currPoint geom type: " + str(currPoint.x()), tag="TOMs panel")

            if sourceLineLayer == snapLineLayer:
                nearestPoint = self.findNearestPointL_2(currPoint, currRestriction, snapLineLayer, tolerance)   # returned as QgsFeature
            else:
                nearestPoint = self.findNearestPointL(currPoint, snapLineLayer, tolerance)  # returned as QgsFeature

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

            if sourceLineLayer == snapLineLayer:
                nearestPoint = self.findNearestPointL_2(currPoint, currRestriction, snapLineLayer, tolerance)   # returned as QgsFeature
            else:
                nearestPoint = self.findNearestPointL(currPoint, snapLineLayer, tolerance)  # returned as QgsFeature

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
                QgsMessageLog.logMessage("Error: snapNodesL: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                    sourceLineLayer.commitErrors()))
                reply = QMessageBox.information(None, "Error",
                                                "SnapNodes: Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                    sourceLineLayer.commitErrors()),
                                                QMessageBox.Ok)
                return

        return

    def snapVertices(self, sourceLineLayer, snapLineLayer, tolerance):
        # For each vertex within restriction, get nearest point on snapLineLayer ...
        QgsMessageLog.logMessage("In snapVertices. Snapping " + sourceLineLayer.name() + " to " + snapLineLayer.name(), tag="TOMs panel")
        QgsMessageLog.logMessage("In snapVertices. " + str(sourceLineLayer.featureCount()) + " features in " + sourceLineLayer.name(), tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        if editStartStatus is False:
            # save the active layer
            QgsMessageLog.logMessage("Error: snapVertices: Not able to start transaction on " + sourceLineLayer.name())
            reply = QMessageBox.information(None, "Error",
                                            "Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        for currRestriction in sourceLineLayer.getFeatures():

            """QgsMessageLog.logMessage(
                "In snapVertices. Considering " + str(currRestriction.attribute("GeometryID")),
                tag="TOMs panel")"""

            geom = currRestriction.geometry()

            if currRestriction.geometry() is None:
                continue

            for vertexNr, vertexPt in enumerate(geom.asPolyline()):

                nearestPoint = self.findNearestPointL(vertexPt, snapLineLayer, tolerance)

                if nearestPoint:
                    # Move the vertex
                    """QgsMessageLog.logMessage("Moving vertex " + str(vertexNr) + " for " + str(currRestriction.attribute("GeometryID")),
                                             tag="TOMs panel")"""
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
            QgsMessageLog.logMessage("Error: snapVertices: Changes to " + sourceLineLayer.name() + " failed: " + str(
                sourceLineLayer.commitErrors()))
            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()),
                                            QMessageBox.Ok)


    def findNearestPointP(self, searchPt, pointLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the given point layer
        # returns QgsPoint
        #QgsMessageLog.logMessage("In findNearestPointP - pointLayer", tag="TOMs panel")

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

        QgsMessageLog.logMessage("In findNearestPointP: shortestDistance: " + str(shortestDistance), tag="TOMs panel")

        del request
        del searchRect

        if shortestDistance < float("inf"):

            QgsMessageLog.logMessage("In findNearestPointP: closestPoint {}".format(nearestPoint.geometry().exportToWkt()),
                                     tag="TOMs panel")

            return nearestPoint   # returns a geometry
        else:
            return None


    def findNearestPointL(self, searchPt, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        QgsMessageLog.logMessage("In findNearestPointL. Checking lineLayer: " + lineLayer.name(), tag="TOMs panel")
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

        #QgsMessageLog.logMessage("In findNearestPointL: shortestDistance: " + str(shortestDistance), tag="TOMs panel")

        del request
        del searchRect

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            #QgsMessageLog.logMessage("findNearestPointL: nearestPoint geom type: " + str(nearestPoint.wkbType()), tag="TOMs panel")
            return closestPoint   # returns a geometry
        else:
            return None

    def findNearestPointL_2(self, searchPt, currRestriction, lineLayer, tolerance):
        # given a point, find the nearest point (within the tolerance) within the line layer
        # returns QgsPoint
        QgsMessageLog.logMessage("In findNearestPointL_2. Checking lineLayer: " + lineLayer.name(), tag="TOMs panel")
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

                    QgsMessageLog.logMessage(
                        "In findNearestPointL_2. Found point: f.id: " + str(f.id()) + " curr_id: " + str(
                            currRestriction.id()),
                        tag="TOMs panel")

                    QgsMessageLog.logMessage("In findNearestPointL_2. Setting distance ..." + str(dist), tag="TOMs panel")

                    if dist < shortestDistance:
                        shortestDistance = dist
                        closestPoint = f.geometry().vertexAt(vertex)

        #QgsMessageLog.logMessage("In findNearestPointL: shortestDistance: " + str(shortestDistance), tag="TOMs panel")

        del request
        del searchRect

        if shortestDistance < float("inf"):
            #nearestPoint = QgsFeature()
            # add the geometry to the feature,
            #nearestPoint.setGeometry(QgsGeometry(closestPtOnFeature))
            #QgsMessageLog.logMessage("findNearestPointL: nearestPoint geom type: " + str(nearestPoint.wkbType()), tag="TOMs panel")
            return QgsGeometry.fromPoint(closestPoint)   # returns a geometry
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
        QgsMessageLog.logMessage("In findNearestLine - lineLayer: " + lineLayer.name() + "; x:" + str(searchPt.x()), tag="TOMs panel")
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

        del request
        del searchRect

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

            """ QgsMessageLog.logMessage("In TraceRestriction2. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel") """

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom.isEmpty():
                QgsMessageLog.logMessage(
                    "In TraceRestriction2. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    tag="TOMs panel")
                continue

            nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

            # Check that this is not a circular feature, i.e., with the end points close to each other. If it is, it will cause some difficulties ...
            if self.circularFeature(currRestriction, tolerance):
                continue  # move to the next feature

            nearestLine = self.nearbyLineFeature(currRestrictionGeom, snapLineLayer, DUPLICATE_POINT_DISTANCE)

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
                            QgsMessageLog.logMessage("In TraceRestriction2: adding vertex " + str(currVertexNr), tag="TOMs panel")
                            newGeometryCoordsList.append(vertexA)
                            countNewVertices = countNewVertices + 1
                    else:  # first pass
                        newGeometryCoordsList.append(vertexA)
                        countNewVertices = countNewVertices + 1

                    # Does this segement lie on the Snapline? and if it lies within the buffer
                    # TODO: What happens if the trace line stops ... (perhaps check for the start/end)

                    if self.pointsOnLine(vertexA, vertexB, nearestLineGeom, DUPLICATE_POINT_DISTANCE) and \
                            self.lineInBuffer(vertexA, vertexB, nearestLineGeom, tolerance):

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

                        # NB: countDirectionAscending only required once for each restriction

                        if countDirectionAscending == None:
                            # TODO: Getting errors with countDirection at start/end of line due (perhaps) to snapping issues. Would be better to check the countDirection over the length of the line??
                            countDirectionAscending = self.findCountDirection(distToA, distToB, lengthSnapLine, lengthAB)

                        QgsMessageLog.logMessage("In TraceRestriction2: ******  countDirectionAscending " + str(countDirectionAscending), tag="TOMs panel")

                        # get closest vertices ...  NB: closestVertex returns point with nearest distance not necessarily "along the line", e.g., in a cul-de-sac

                        includeVertexAfterA, vertexNrAfterA, includeVertexAfterB, \
                            vertexNrAfterB = self.checkNeighbouringVertices(vertexA, vertexB, nearestLineGeom,
                                                                                countDirectionAscending, distToA, distToB)
                        # Now add relevant kerb vertices to restriction

                        currSnapLineVertex = nearestLineGeom.asPolyline()[vertexNrAfterA]
                        currSnapLineVertexNr = vertexNrAfterA

                        QgsMessageLog.logMessage("In TraceRestriction2: ****** START nearestVertexAfterA " + str(vertexNrAfterA) + "; curr " + str(currSnapLineVertexNr) + " B: " + str(vertexNrAfterB), tag="TOMs panel")
                        #QgsMessageLog.logMessage("In TraceRestriction2: ****** START vertexNrAfterA " + str(vertexNrAfterA) + " vertexNrAfterB: " + str(vertexNrAfterB), tag="TOMs panel")
                        QgsMessageLog.logMessage("In TraceRestriction2: ******  includeVertexAfterA " + str(includeVertexAfterA) + "; includeVertexAfterB " + str(includeVertexAfterB), tag="TOMs panel")

                        if includeVertexAfterA:

                            QgsMessageLog.logMessage(
                                "In TraceRestriction2: includeVertexAfterA: " + str(currSnapLineVertexNr) + " currSnapLineVertex: " + str(currSnapLineVertex.x()) + "," + str(currSnapLineVertex.y()), tag="TOMs panel")
                            QgsMessageLog.logMessage("In TraceRestriction2: includeVertexAfterA: vertexA: " + str(vertexA.x()) + "," + str(vertexA.y()), tag="TOMs panel")

                            if not self.duplicatePoint(vertexA, currSnapLineVertex):
                                if not self.duplicatePoint(vertexB, currSnapLineVertex):
                                    newGeometryCoordsList.append(currSnapLineVertex)
                                    countNewVertices = countNewVertices + 1
                                    QgsMessageLog.logMessage("In TraceRestriction2: ... including trace line vertex " + str(currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices), tag="TOMs panel")

                            """status = self.insertVertexIntoRestriction(newGeometryCoordsList, curSnapLineVertex)
                            if status == True:
                                newGeometryVertexNr = newGeometryVertexNr + 1
                            else:
                                reply = QMessageBox.information(None, "Error",
                                                                "TraceRestriction2: Problem adding nearestVertexToA ",
                                                                QMessageBox.Ok)"""
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
                                QgsMessageLog.logMessage("In TraceRestriction2: ... including trace line vertex " + str(currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices), tag="TOMs panel")
                                QgsMessageLog.logMessage("In TraceRestriction2: vertexNrAfterA " + str(vertexNrAfterA) + "; curr " + str(currSnapLineVertexNr) + " vertexNrAfterB: " + str(vertexNrAfterB), tag="TOMs panel")

                            """if countNewVertices > 1000:
                                break"""

                    # Insert Vertex B. This is the final point in the line - check for duplication ...
                    if countNewVertices > 1:
                        if self.duplicatePoint(vertexB, newGeometryCoordsList[-1]):
                            newGeometryCoordsList[-1] = vertexB
                            QgsMessageLog.logMessage("In TraceRestriction2: overwriting last vertex ...", tag="TOMs panel")
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
                """QgsMessageLog.logMessage("In TraceRestriction2. " + str(currRestriction.attribute("GeometryID")) +
                                         ": geometry changed ***. New nrVertices " + str(countNewVertices), tag="TOMs panel")"""
                QgsMessageLog.logMessage("In TraceRestriction2: new geom: " + str(currRestriction.geometry().exportToWkt()),
                                         tag="TOMs panel")
                """QgsMessageLog.logMessage(
                    "In TraceRestriction2. " + str(currRestriction.attribute(
                        "GeometryID")) + ": geometry changed ***. New nrVertices " + str(
                        countNewVertices) + "; OrigLen: " + str(lengthAB) + " newLen: " + str(newShape.length()), tag="TOMs panel")"""

        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    """
    ****** Approach whcih calculates shortest route between then snaps to that
    """

    def setupTrace(self, sourceLineLayer):

        self.director = QgsVectorLayerDirector(sourceLineLayer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
        strategy = QgsNetworkDistanceStrategy()
        self.director.addStrategy(strategy)
        self.builder = QgsGraphBuilder(sourceLineLayer.crs())

    def getShortestPath(self, startPoint, endPoint):
        # taken from Qgis Py Cookbook
        #startPoint = self.ptList[0][0].asPoint()
        #endPoint = self.ptList[1][0].asPoint()

        tiedPoints = self.director.makeGraph(self.builder, [startPoint, endPoint])
        tStart, tStop = tiedPoints

        graph = self.builder.graph()
        idxStart = graph.findVertex(tStart)

        tree = QgsGraphAnalyzer.shortestTree(graph, idxStart, 0)

        idxStart = tree.findVertex(tStart)
        idxEnd = tree.findVertex(tStop)

        if idxEnd == -1:
            raise Exception('No route!')

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

    def TraceRestriction3(self, sourceLineLayer, snapLineLayer, tolerance):

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

        # set up shortest path checker
        self.setupTrace(sourceLineLayer)

        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            """ QgsMessageLog.logMessage("In TraceRestriction2. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel") """

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom.isEmpty():
                QgsMessageLog.logMessage(
                    "In TraceRestriction2. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    tag="TOMs panel")
                continue

            nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

            # Check that this is not a circular feature, i.e., with the end points close to each other. If it is, it will cause some difficulties ...
            if self.circularFeature(currRestriction, tolerance):
                continue  # move to the next feature

            #nearestLine = self.nearbyLineFeature(currRestrictionGeom, snapLineLayer, DUPLICATE_POINT_DISTANCE)

            """ *** """
            if nrVerticesInCurrRestriction >= 2:
                # we can now display the line - taken from Qgis Py Cookbook
                ptList = currRestrictionGeom.asPolyline()
                startPt = QgsPoint(ptList[0])
                endPt = QgsPoint(ptList[-1])

                QgsMessageLog.logMessage("In foundLinkForLine::startPt " + startPt.asWkt(), tag="TOMs panel")
                QgsMessageLog.logMessage("In foundLinkForLine::endPt " + endPt.asWkt(), tag="TOMs panel")

                route = self.showShortestPath(startPt, endPt)

            """ *** """
            if route:

                # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

                QgsMessageLog.logMessage(
                    "In TraceRestriction3. nearest line found. Considering " + str(
                        len(currRestrictionGeom.asPolyline())) + " points",
                    tag="TOMs panel")
                #nearestLineGeom = nearestLine.geometry()
                nearestLineGeom = route

                # initialise a new Geometry
                newGeometryCoordsList = []
                # newGeometryVertexNr = 0
                countDirectionAscending = None
                nrVerticesInSnapLine = len(nearestLineGeom.asPolyline())
                lengthSnapLine = nearestLineGeom.length()
                countNewVertices = 0


                """ ***
                Logic is:
                a. assume that there are not duplicate points in the source geometry
                b. trace against the shortest path line along the kerb and assume that it is going in the same direction
                
                
                step through each line segement in sourceLine:
                    see if it is within tolerance of the line
                    step through each line segement of the trace line ...
                    
                *** """

                for currVertexNr, currVertexPt in enumerate(currRestrictionGeom.asPolyline()):

                    # Check we haven't reached the last vertex
                    if currVertexNr == (nrVerticesInCurrRestriction - 1):
                        break

                    # Now consider line segment
                    vertexA = currVertexPt
                    vertexB = currRestrictionGeom.asPolyline()[currVertexNr + 1]
                    currDeltaX = vertexB.x() - vertexA.x()
                    currDeltaX = vertexB.y() - vertexA.y()

                    # Insert Vertex A. NB: don't want to duplicate points  *** Assume that there are no duplicates
                    """if countNewVertices > 1:
                        if not self.duplicatePoint(vertexA, newGeometryCoordsList[-1]):
                            QgsMessageLog.logMessage("In TraceRestriction2: adding vertex " + str(currVertexNr),
                                                     tag="TOMs panel")
                            newGeometryCoordsList.append(vertexA)
                            countNewVertices = countNewVertices + 1
                    else:  # first pass
                        newGeometryCoordsList.append(vertexA)
                        countNewVertices = countNewVertices + 1"""

                    # Does this segement lie on the Snapline? and if it lies within the buffer
                    # TODO: What happens if the trace line stops ... (perhaps check for the start/end)

                    if self.pointsOnLine(vertexA, vertexB, nearestLineGeom, DUPLICATE_POINT_DISTANCE) and \
                            self.lineInBuffer(vertexA, vertexB, nearestLineGeom, tolerance):

                        QgsMessageLog.logMessage(
                            "In TraceRestriction2. " + str(
                                currRestriction.attribute(
                                    "GeometryID")) + ": considering segment between " + str(
                                currVertexNr) + " and " + str(currVertexNr + 1),
                            tag="TOMs panel")

                        # we have a line segement that needs to be traced. Set upi relevant variables

                        lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
                        lengthAB = lineAB_Geom.length()

                        distToA = nearestLineGeom.lineLocatePoint(
                            QgsGeometry.fromPoint(vertexA))  # QgsGeometry of point ??
                        distToB = nearestLineGeom.lineLocatePoint(QgsGeometry.fromPoint(vertexB))

                        # NB: countDirectionAscending only required once for each restriction

                        if countDirectionAscending == None:
                            # TODO: Getting errors with countDirection at start/end of line due (perhaps) to snapping issues. Would be better to check the countDirection over the length of the line??
                            countDirectionAscending = self.findCountDirection(distToA, distToB, lengthSnapLine,
                                                                              lengthAB)

                        QgsMessageLog.logMessage(
                            "In TraceRestriction2: ******  countDirectionAscending " + str(countDirectionAscending),
                            tag="TOMs panel")

                        # get closest vertices ...  NB: closestVertex returns point with nearest distance not necessarily "along the line", e.g., in a cul-de-sac

                        includeVertexAfterA, vertexNrAfterA, includeVertexAfterB, \
                        vertexNrAfterB = self.checkNeighbouringVertices(vertexA, vertexB, nearestLineGeom,
                                                                        countDirectionAscending, distToA, distToB)
                        # Now add relevant kerb vertices to restriction

                        currSnapLineVertex = nearestLineGeom.asPolyline()[vertexNrAfterA]
                        currSnapLineVertexNr = vertexNrAfterA

                        QgsMessageLog.logMessage("In TraceRestriction2: ****** START nearestVertexAfterA " + str(
                            vertexNrAfterA) + "; curr " + str(currSnapLineVertexNr) + " B: " + str(vertexNrAfterB),
                                                 tag="TOMs panel")
                        # QgsMessageLog.logMessage("In TraceRestriction2: ****** START vertexNrAfterA " + str(vertexNrAfterA) + " vertexNrAfterB: " + str(vertexNrAfterB), tag="TOMs panel")
                        QgsMessageLog.logMessage("In TraceRestriction2: ******  includeVertexAfterA " + str(
                            includeVertexAfterA) + "; includeVertexAfterB " + str(includeVertexAfterB),
                                                 tag="TOMs panel")

                        if includeVertexAfterA:

                            QgsMessageLog.logMessage(
                                "In TraceRestriction2: includeVertexAfterA: " + str(
                                    currSnapLineVertexNr) + " currSnapLineVertex: " + str(
                                    currSnapLineVertex.x()) + "," + str(currSnapLineVertex.y()), tag="TOMs panel")
                            QgsMessageLog.logMessage(
                                "In TraceRestriction2: includeVertexAfterA: vertexA: " + str(vertexA.x()) + "," + str(
                                    vertexA.y()), tag="TOMs panel")

                            if not self.duplicatePoint(vertexA, currSnapLineVertex):
                                if not self.duplicatePoint(vertexB, currSnapLineVertex):
                                    newGeometryCoordsList.append(currSnapLineVertex)
                                    countNewVertices = countNewVertices + 1
                                    QgsMessageLog.logMessage(
                                        "In TraceRestriction2: ... including trace line vertex " + str(
                                            currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices),
                                        tag="TOMs panel")

                            """status = self.insertVertexIntoRestriction(newGeometryCoordsList, curSnapLineVertex)
                            if status == True:
                                newGeometryVertexNr = newGeometryVertexNr + 1
                            else:
                                reply = QMessageBox.information(None, "Error",
                                                                "TraceRestriction2: Problem adding nearestVertexToA ",
                                                                QMessageBox.Ok)"""
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
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[nrVerticesInSnapLine - 1]
                                    currSnapLineVertexNr = nrVerticesInSnapLine - 1
                                else:
                                    currSnapLineVertex = nearestLineGeom.asPolyline()[currSnapLineVertexNr]

                            if currSnapLineVertexNr == vertexNrAfterB:
                                stopped = True  # set stop flag for loop
                                if includeVertexAfterB == False:
                                    break

                            # add the vertex - check first to see if it duplicates the previous point

                            if not self.duplicatePoint(newGeometryCoordsList[countNewVertices - 1], currSnapLineVertex):
                                newGeometryCoordsList.append(currSnapLineVertex)
                                countNewVertices = countNewVertices + 1
                                QgsMessageLog.logMessage("In TraceRestriction2: ... including trace line vertex " + str(
                                    currSnapLineVertexNr) + " : countNewVertices " + str(countNewVertices),
                                                         tag="TOMs panel")
                                QgsMessageLog.logMessage(
                                    "In TraceRestriction2: vertexNrAfterA " + str(vertexNrAfterA) + "; curr " + str(
                                        currSnapLineVertexNr) + " vertexNrAfterB: " + str(vertexNrAfterB),
                                    tag="TOMs panel")

                            """if countNewVertices > 1000:
                                break"""

                    # Insert Vertex B. This is the final point in the line - check for duplication ...
                    if countNewVertices > 1:
                        if self.duplicatePoint(vertexB, newGeometryCoordsList[-1]):
                            newGeometryCoordsList[-1] = vertexB
                            QgsMessageLog.logMessage("In TraceRestriction2: overwriting last vertex ...",
                                                     tag="TOMs panel")
                        else:
                            newGeometryCoordsList.append(vertexB)
                            countNewVertices = countNewVertices + 1
                    else:
                        newGeometryCoordsList.append(vertexB)
                        countNewVertices = countNewVertices + 1

                # Now replace the orginal geometry of the current restriction with the new geometry
                # currRestriction.setGeometry(QgsGeometry.fromPolyline(newGeometryCoordsList))

                newShape = QgsGeometry.fromPolyline(newGeometryCoordsList)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)
                """QgsMessageLog.logMessage("In TraceRestriction2. " + str(currRestriction.attribute("GeometryID")) +
                                         ": geometry changed ***. New nrVertices " + str(countNewVertices), tag="TOMs panel")"""
                QgsMessageLog.logMessage(
                    "In TraceRestriction2: new geom: " + str(currRestriction.geometry().exportToWkt()),
                    tag="TOMs panel")
                """QgsMessageLog.logMessage(
                    "In TraceRestriction2. " + str(currRestriction.attribute(
                        "GeometryID")) + ": geometry changed ***. New nrVertices " + str(
                        countNewVertices) + "; OrigLen: " + str(lengthAB) + " newLen: " + str(newShape.length()), tag="TOMs panel")"""

        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    """ ***** """


    def duplicatePoint(self, pointA, pointB):

        duplicate = False

        if pointA is None or pointB is None:
            duplicate = False
        elif math.sqrt((pointA.x() - pointB.x())**2 + ((pointA.y() - pointB.y())**2)) < DUPLICATE_POINT_DISTANCE:
            duplicate = True

        return duplicate

    def circularFeature(self, currRestriction, lineTolerance):

        QgsMessageLog.logMessage("In circularFeature", tag="TOMs panel")

        currRestrictionGeom = currRestriction.geometry()

        nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())

        startVertex = currRestrictionGeom.asPolyline()[0]
        endVertex = currRestrictionGeom.asPolyline()[nrVerticesInCurrRestriction-1]

        dist = QgsGeometry.fromPoint(startVertex).distance(QgsGeometry.fromPoint(endVertex))

        if (dist <= lineTolerance):
            """QgsMessageLog.logMessage("In circularFeature: Circular feature found: " + currRestriction.attribute(
                        "GeometryID"), tag="TOMs panel")"""
            return True
        else:
            return False

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

    def lineInBuffer(self, vertexA, vertexB, nearestLineGeom, bufferWidth):

        QgsMessageLog.logMessage("In lineInBuffer", tag="TOMs panel")

        isWithin = False

        lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
        bufferGeom = nearestLineGeom.buffer(bufferWidth, 5)

        if lineAB_Geom.within(bufferGeom):
            isWithin = True

        return isWithin

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
            QgsGeometry.fromPoint(nearestLineGeom.asPolyline()[vertexNrAfterA]))  # QgsPoint
        distVertexAfterB = nearestLineGeom.lineLocatePoint(
            QgsGeometry.fromPoint(nearestLineGeom.asPolyline()[vertexNrAfterB]))
        # Work out whether or not nearest vertices need to be included …

        includeVertexAfterA = False
        includeVertexAfterB = False

        QgsMessageLog.logMessage(
            "In checkNeighbouringVertices: --- vertexNrAfterA " + str(vertexNrAfterA) + "; vertexNrAfterB: " + str(vertexNrAfterB), tag="TOMs panel")
        QgsMessageLog.logMessage(
            "In checkNeighbouringVertices: --- distVertexAfterA " + str(distVertexAfterA) + ": distToA " + str(distToA) + "; distVertexAfterB: " + str(distVertexAfterB) + ": distToB " + str(distToB), tag="TOMs panel")

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

    def removePointsOutsideTolerance(self, sourceLineLayer, snapLineLayer, tolerance):
        # function to remove duplicate points or ones that are colinear (?) or at least ones that double back

        QgsMessageLog.logMessage("In removePointsOutsideTolerance", tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        """reply = QMessageBox.information(None, "Check",
                                        "removeDuplicatePoints: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)"""

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "removePointsOutsideTolerance: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return
        # Read through each restriction and compare each point

        # For each restriction in layer
        for currRestriction in sourceLineLayer.getFeatures():

            restGeom = currRestriction.geometry()
            """QgsMessageLog.logMessage(
                "In removePointsOutsideTolerance. Considering " + str(currRestriction.attribute("GeometryID")),
                tag="TOMs panel")"""
            QgsMessageLog.logMessage(
                "In removePointsOutsideTolerance. Considering " + str(currRestriction.id()),
                tag="TOMs panel")

            if restGeom is None:
                continue

            line = currRestriction.geometry().asPolyline()

            for vertexNr in range(len(line)):

                QgsMessageLog.logMessage("In removePointsOutsideTolerance. Considering vertex " + str(vertexNr), tag="TOMs panel")
                vertexPt = line[vertexNr]

                nearestLine = self.findNearestLine(vertexPt, snapLineLayer, tolerance)
                """ If there is no line within tolerance, then it can be deleted """
                if nearestLine is None:
                    sourceLineLayer.deleteVertex(currRestriction.id(), vertexNr)
                    QgsMessageLog.logMessage("In removePointsOutsideTolerance. Deleting vertex " + str(vertexNr), tag="TOMs panel")

            pass

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

            QgsMessageLog.logMessage("In removeDuplicates2. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel")

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom is None:
                continue

            nrVerticesInCurrRestriction = len(currRestrictionGeom.asPolyline())


            # initialise a new Geometry
            newGeometryCoordsList = []
            countNewVertices = 0
            distLastVertex = 0.0

            line = currRestrictionGeom.asPolyline()

            # for currVertexNr, currVertexPt in enumerate(currRestrictionGeom.asPolyline()):
            for currVertexPt in line:

                """QgsMessageLog.logMessage("In removeDuplicates. *** considering vertex: " + str(currVertexNr),
                                         tag="TOMs panel")"""

                if countNewVertices == 0:
                    newGeometryCoordsList.append(currVertexPt)
                    countNewVertices = countNewVertices + 1

                else:
                    if self.duplicatePoint(newGeometryCoordsList[countNewVertices-1], currVertexPt) is not True:
                        newGeometryCoordsList.append(currVertexPt)
                        countNewVertices = countNewVertices + 1

                # Check we haven't reached the last vertex
                #if currVertexNr == (nrVerticesInCurrRestriction - 1):
                #    break

                # add the vertex - check first to see if it duplicates the previous point

                #distCurrVertex = currRestrictionGeom.lineLocatePoint(QgsGeometry.fromPoint(currVertexPt))



                # if self.duplicatePoint(newGeometryCoordsList[countNewVertices-1], currVertexPt)
                """if countNewVertices > 0:

                    if not self.duplicatePoint(newGeometryCoordsList[countNewVertices-1], currVertexPt):

                        if countNewVertices > 1:

                            lineCurrPrev = QgsGeometry.fromPolyline([prevVertexPt, currVertexPt])
                            linePrevButOne = QgsGeometry.fromPolyline([prevButOneVertexPt, prevVertexPt])

                            if not lineCurrPrev.intersects(linePrevButOne):
                                newGeometryCoordsList.append(currVertexPt)
                                countNewVertices = countNewVertices + 1
                                QgsMessageLog.logMessage("In removeDuplicates. *** vertex added (non-dup, non-int): " + str(countNewVertices), tag="TOMs panel")

                        else:

                            newGeometryCoordsList.append(currVertexPt)
                            countNewVertices = countNewVertices + 1
                            QgsMessageLog.logMessage("In removeDuplicates. *** vertex added (non-dup 2nd): " + str(countNewVertices), tag="TOMs panel")

                else:
                    newGeometryCoordsList.append(currVertexPt)
                    countNewVertices = countNewVertices + 1
                    prevVertexPt = currVertexPt  # set to avoid null error
                    QgsMessageLog.logMessage("In removeDuplicates. *** vertex added (first point): " + str(countNewVertices),
                                         tag="TOMs panel")
                #distLastVertex = distCurrVertex
                prevButOneVertexPt = prevVertexPt
                prevVertexPt = currVertexPt"""

            # Insert Vertex B. This is the final point in the line - check for duplication ...
            """if self.duplicatePoint(currVertexPt, newGeometryCoordsList[-1]) and countNewVertices > 1:
                newGeometryCoordsList[-1] = currVertexPt
                QgsMessageLog.logMessage("In TraceRestriction2: overwriting last vertex ...", tag="TOMs panel")
            else:
                newGeometryCoordsList.append(currVertexPt)
                countNewVertices = countNewVertices + 1"""

            # Now replace the orginal geometry of the current restriction with the new geometry
            #currRestriction.setGeometry(QgsGeometry.fromPolyline(newGeometryCoordsList))

            if countNewVertices <> nrVerticesInCurrRestriction and countNewVertices > 1:
                newShape = QgsGeometry.fromPolyline(newGeometryCoordsList)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)
                QgsMessageLog.logMessage("In removeDuplicates2. " + str(currRestriction.attribute("GeometryID")) +
                                         ": geometry changed ***. New nrVertices " + str(countNewVertices), tag="TOMs panel")
                QgsMessageLog.logMessage("In removeDuplicates2: new geom: " + str(currRestriction.geometry().exportToWkt()),
                                         tag="TOMs panel")


        #editCommitStatus = sourceLineLayer.commitChanges()

        editCommitStatus = False

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

    def checkOverlaps(self, sourceLineLayer, tolerance):

        """ This is really to check whether or not there is a problem with the trace tool """

        QgsMessageLog.logMessage("In checkOverlaps " + sourceLineLayer.name(), tag="TOMs panel")

        editStartStatus = sourceLineLayer.startEditing()

        reply = QMessageBox.information(None, "Check",
                                        "checkOverlaps: Status for starting edit session on " + sourceLineLayer.name() + " is: " + str(
                                            editStartStatus),
                                        QMessageBox.Ok)

        if editStartStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "checkOverlaps: Not able to start transaction on " + sourceLineLayer.name(),
                                            QMessageBox.Ok)
            return

        for currRestriction in sourceLineLayer.getFeatures():

            # get nearest snapLineLayer feature (using the second vertex as the test)

            QgsMessageLog.logMessage("In checkOverlaps. Considering: " + str(currRestriction.attribute("GeometryID")), tag = "TOMs panel")

            currRestrictionGeom = currRestriction.geometry()
            if currRestrictionGeom.isEmpty():
                QgsMessageLog.logMessage(
                    "In TraceRestriction2. NO GEOMETRY FOR: " + str(currRestriction.attribute("GeometryID")),
                    tag="TOMs panel")
                continue

            currRestrictionPtsList = currRestrictionGeom.asPolyline()
            nrVerticesInCurrRestriction = len(currRestrictionPtsList)

            currVertexNr = 1
            vertexA = currRestrictionPtsList[0]
            shapeChanged = False

            QgsMessageLog.logMessage("In checkOverlaps. nrVertices: " + str(nrVerticesInCurrRestriction), tag = "TOMs panel")

            # Now, consider each vertex of the sourceLineLayer in turn - and create new geometry

            while currVertexNr < (nrVerticesInCurrRestriction-1):

                vertexB = currRestrictionPtsList[currVertexNr]
                vertexC = currRestrictionPtsList[currVertexNr + 1]

                if self.LineOverlaps(vertexA, vertexB, vertexC):

                    QgsMessageLog.logMessage("In checkOverlaps. found overlaps at " + str(currVertexNr),
                                             tag="TOMs panel")
                    # do not want currVertex within new restriction
                    currRestrictionPtsList.remove(currRestrictionPtsList[currVertexNr])
                    nrVerticesInCurrRestriction = len(currRestrictionPtsList)
                    shapeChanged = True
                    QgsMessageLog.logMessage("In checkOverlaps. removing vertex" + str(currVertexNr),
                                             tag="TOMs panel")
                    if currVertexNr > 1:
                        currVertexNr = currVertexNr - 1

                    vertexA = currRestrictionPtsList[currVertexNr-1]

                else:

                    vertexA = vertexB
                    currVertexNr = currVertexNr + 1

            if shapeChanged:
                QgsMessageLog.logMessage("In checkOverlaps. changes written ... ",
                                         tag="TOMs panel")
                newShape = QgsGeometry.fromPolyline(currRestrictionPtsList)
                sourceLineLayer.changeGeometry(currRestriction.id(), newShape)


        QgsMessageLog.logMessage("In checkOverlaps. Now finished layer ... ",
                                         tag="TOMs panel")
        editCommitStatus = False

        if editCommitStatus is False:
            # save the active layer

            reply = QMessageBox.information(None, "Error",
                                            "Changes to " + sourceLineLayer.name() + " failed: " + str(
                                                sourceLineLayer.commitErrors()), QMessageBox.Ok)

    """ ***** """

    def lineOverlaps(self, vertexA, vertexB, vertexC):

        prevDeltaX = vertexB.x() - vertexA.x()
        prevDeltaY = vertexB.y() - vertexA.y()
        currDeltaX = vertexC.x() - vertexB.x()
        currDeltaY = vertexC.y() - vertexB.y()

        dotProduct = currDeltaX * prevDeltaX + currDeltaY * prevDeltaY

        if dotProduct < 0:
            # candidate for overlap
            lineAB_Geom = QgsGeometry.fromPolyline([vertexA, vertexB])
            lineBC_Geom = QgsGeometry.fromPolyline([vertexB, vertexC])

            if lineBC_Geom.overlaps(lineAB_Geom):
                return True

        return False