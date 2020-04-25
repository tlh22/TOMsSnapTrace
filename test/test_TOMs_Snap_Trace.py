# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'th@mhtc.co.uk'
__date__ = '2017-12-15'
__copyright__ = 'Copyright 2017, TH'

import unittest

#from PyQt4.QtGui import QDialogButtonBox, QDialog
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget, QDialog
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
    QgsApplication, QgsRectangle, QgsPoint, QgsPointXY, QgsVectorLayer
)


"""from qgis.testing import (
    start_app,
    unittest,
)

from utilities import (
    compareWkt,
    unitTestDataPath,
    writeShape
)
start_app()
TEST_DATA_DIR = unitTestDataPath()
"""

from TOMs_Snap_Trace import TOMsSnapTrace, SnapTraceUtils

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()



"""qgs = QgsApplication([], False)
QgsApplication.setPrefixPath("C:\QGIS_310\apps\qgis-ltr", True)
QgsApplication.initQgis()"""

class DummyInterface(object):
    def __getattr__(self, *args, **kwargs):
        def dummy(*args, **kwargs):
            return self
        return dummy
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration
    def layers(self):
        # simulate iface.legendInterface().layers()
        return QgsProject.instance().mapLayersByName()

iface = DummyInterface()

class TOMsSnapTraceTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        #self.dialog = TOMsSnapTraceDialog(None)
        #QGIS_APP, CANVAS, iface, PARENT = get_qgis_app()
        #iface = DummyInterface()

        self.testClass = SnapTraceUtils()
        pass

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def testStartEndPoints(self):
        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        testFeature = QgsFeature()
        testFeature.setGeometry(testLineString)

        result = self.testClass.getStartPoint(testFeature)
        self.assertEqual(result.asWkt(), 'Point (0 0)')

        result = self.testClass.getEndPoint(testFeature)
        self.assertEqual(result.asWkt(), 'Point (3 0)')

    def testFindDuplicatePoint(self):

        pointA = QgsPointXY(0, 0)
        pointB = QgsPointXY(0, 1)
        pointC = QgsPointXY(0, 0.02)
        pointD = QgsPointXY(0, 0.01)
        pointE = None

        result = self.testClass.duplicatePoint(pointA, pointB)
        self.assertFalse(result)

        result = self.testClass.duplicatePoint(pointA, pointC)
        self.assertFalse(result)

        result = self.testClass.duplicatePoint(pointA, pointD)
        self.assertTrue(result)

        result = self.testClass.duplicatePoint(pointA, pointE)
        self.assertFalse(result)

    def testReturnCorrectedGeometryForDuplicatePoint(self):

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        tolerance = 0.02

        # no duplicates
        result = self.testClass.checkRestrictionGeometryForDuplicatePoints(testLineString, tolerance)
        self.assertFalse(result)

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(0, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        # one duplicate
        result = self.testClass.checkRestrictionGeometryForDuplicatePoints(testLineString, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 2 0, 3 0)')

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(0, 0), QgsPointXY(2, 0), QgsPointXY(2, 0)]
        )
        # two duplicates
        result = self.testClass.checkRestrictionGeometryForDuplicatePoints(testLineString, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 2 0)')

    def testFindSelfOverlap(self):

        """

        2-+-+-+-+-1+-+-+-+-0+-+-+-+-3

        """


        polyline = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0)]
        )

        # check no horizontal overlap
        result = self.testClass.lineOverlaps(QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0))
        self.assertFalse(result)

        # check no vertical overlap
        result = self.testClass.lineOverlaps(QgsPointXY(0, 0), QgsPointXY(0, -1), QgsPointXY(0, -2))
        self.assertFalse(result)

        # check no oblique overlap
        result = self.testClass.lineOverlaps(QgsPointXY(0, 0), QgsPointXY(-1, -1), QgsPointXY(-2, -2))
        self.assertFalse(result)

        # check no overlap for right angle
        result = self.testClass.lineOverlaps(QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-1, -1))
        self.assertFalse(result)

        # check no overlap for acute angle
        result = self.testClass.lineOverlaps(QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(0, -1))
        self.assertFalse(result)

        # horizontal overlap
        result = self.testClass.lineOverlaps(QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0))
        self.assertTrue(result)

        # vertical overlap
        result = self.testClass.lineOverlaps(QgsPointXY(0,-1), QgsPointXY(0, -2), QgsPointXY(0, 1))
        self.assertTrue(result)

        # oblique overlap
        result = self.testClass.lineOverlaps(QgsPointXY(-1,-1), QgsPointXY(-2, -2), QgsPointXY(1, 1))
        self.assertTrue(result)

    def testReturnCorrectedGeometryForSelfOverlap(self):

        """

        2-+-+-+-+-1+-+-+-+-0+-+-+-+-3

        """


        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 1)]
        )

        # with no overlap
        result = self.testClass.checkRestrictionGeometryForSelfOverlap(testLineString)
        self.assertFalse(result)
        #self.assertEqual(result.asWkt(), 'LineString (10 10, 20 10, 30 10)')
        #print ('Test 2.2')

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0)]
        )
        # with overlap at start
        result = self.testClass.checkRestrictionGeometryForSelfOverlap(testLineString)
        #print (result)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0)')

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0), QgsPointXY(3, 0), QgsPointXY(2.5, 0), QgsPointXY(2, 0)]
        )
        # with overlap at start
        result = self.testClass.checkRestrictionGeometryForSelfOverlap(testLineString)
        #print (result)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0, 2 0)')

    def testCheckRestrictionGeometryForSnappedNodes(self):

        tolerance = 0.4

        testLayer = QgsVectorLayer(
            ('LineString?crs=epsg:27700&field=name:string(20)&index=yes'),
            'test1',
            'memory')
        testProvider = testLayer.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        testLineString2 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 1), QgsPointXY(1, 1), QgsPointXY(2, 1), QgsPointXY(3, 1)]
        )
        testFeature1 = QgsFeature()
        testFeature1.setGeometry(testLineString1)
        testLayer.addFeatures([testFeature1])
        testFeature2 = QgsFeature()
        testFeature2.setGeometry(testLineString2)
        testLayer.addFeatures([testFeature2])

        myResult, myFeatures = testProvider.addFeatures(
            [testFeature1, testFeature2])
        assert myResult
        self.assertEqual(len(myFeatures), 2)
        self.assertEqual(testLayer.featureCount(), 2)
        """for f in testLayer.getFeatures():
            print ('testFeature: {}'.format(f.id()))"""

        # check whether or not there is a nearby line
        result = self.testClass.findNearestPointOnLineLayer(QgsPointXY(0, 0.5), testLayer, tolerance)
        self.assertEqual(result, (None, None))

        closestPoint, closestFeature = self.testClass.findNearestPointOnLineLayer(QgsPointXY(0, 0), testLayer, tolerance)
        self.assertEqual(closestPoint.asWkt(), 'Point (0 0)')
        self.assertEqual(closestFeature.id(), 1)

        closestPoint, closestFeature = self.testClass.findNearestPointOnLineLayer(QgsPointXY(1, 0.2), testLayer, tolerance)
        self.assertEqual(closestPoint.asWkt(), 'Point (1 0)')
        self.assertEqual(closestFeature.id(), 1)

        closestPoint, closestFeature = self.testClass.findNearestPointOnLineLayer(QgsPointXY(2.5, 0.9), testLayer, tolerance)
        self.assertEqual(closestPoint.asWkt(), 'Point (2.5 1)')
        self.assertEqual(closestFeature.id(), 2)

        #find nearest node
        result = self.testClass.findNearestNodeOnLineLayer(QgsPointXY(0, 0.5), testLayer, tolerance)
        self.assertFalse(result)

        result = self.testClass.findNearestNodeOnLineLayer(QgsPointXY(2.8, 0), testLayer, tolerance)
        self.assertEqual(result.asWkt(), 'Point (3 0)')

        # snap to node
        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.5), QgsPointXY(1, 0.5)])
        result = self.testClass.checkRestrictionGeometryForSnappedNodes(currGeom, testLayer, tolerance)
        self.assertFalse(result)

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.5), QgsPointXY(1, 0)])
        result = self.testClass.checkRestrictionGeometryForSnappedNodes(currGeom, testLayer, tolerance)
        self.assertFalse(result)

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.2), QgsPointXY(1, 0.5)])
        result = self.testClass.checkRestrictionGeometryForSnappedNodes(currGeom, testLayer, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0.5)')

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.2), QgsPointXY(1, 0.5), QgsPointXY(2.9, 0.9)])
        result = self.testClass.checkRestrictionGeometryForSnappedNodes(currGeom, testLayer, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0.5, 3 1)')

    def testCheckRestrictionGeometryForSnappedVertices(self):

        tolerance = 0.2

        testLayer = QgsVectorLayer(
            ('LineString?crs=epsg:27700&field=name:string(20)&index=yes'),
            'test1',
            'memory')
        testProvider = testLayer.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        testLineString2 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 1), QgsPointXY(1, 1), QgsPointXY(2, 1), QgsPointXY(3, 1)]
        )
        testFeature1 = QgsFeature()
        testFeature1.setGeometry(testLineString1)
        testLayer.addFeatures([testFeature1])
        testFeature2 = QgsFeature()
        testFeature2.setGeometry(testLineString2)
        testLayer.addFeatures([testFeature2])

        myResult, myFeatures = testProvider.addFeatures(
            [testFeature1, testFeature2])
        assert myResult
        self.assertEqual(len(myFeatures), 2)
        self.assertEqual(testLayer.featureCount(), 2)

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.3), QgsPointXY(1, 0.5), QgsPointXY(2.7, 0.7)])
        result = self.testClass.checkRestrictionGeometryForSnappedVertices(currGeom, testLayer, tolerance)
        self.assertFalse(result)

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0.2), QgsPointXY(0.5, 0.8), QgsPointXY(2, 0.5), QgsPointXY(2, 0.9)])
        result = self.testClass.checkRestrictionGeometryForSnappedVertices(currGeom, testLayer, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 0.5 1, 2 0.5, 2 1)')

    def testCheckRestrictionGeometryForTracedVertices(self):

        tolerance = 0.2
        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )

        #pointOnLine
        result = self.testClass.pointOnLine(QgsPointXY(0, 1), testLineString1)
        self.assertFalse(result)

        result = self.testClass.pointOnLine(QgsPointXY(1.5, 0), testLineString1)
        self.assertEqual(result.asWkt(), 'POINT(1.5 0)')

        # traceRouteGeom
        result = self.testClass.traceRouteGeom(QgsPointXY(0, 0), QgsPointXY(1, 0), testLineString1, tolerance)
        self.assertFalse(result)

        result = self.testClass.traceRouteGeom(QgsPointXY(0.5, 0), QgsPointXY(0.75, 0), testLineString1, tolerance)
        self.assertFalse(result)

        result = self.testClass.traceRouteGeom(QgsPointXY(1, 0), QgsPointXY(2, 0), testLineString1, tolerance)
        self.assertFalse(result)

        result = self.testClass.traceRouteGeom(QgsPointXY(0, 0), QgsPointXY(2, 0), testLineString1, tolerance)
        self.assertEqual(result, [QgsPointXY(1, 0)])

        result = self.testClass.traceRouteGeom(QgsPointXY(0, 0), QgsPointXY(3, 0), testLineString1, tolerance)
        self.assertEqual(result, [QgsPointXY(1, 0), QgsPointXY(2, 0)])

        testLineString2 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(1, 1), QgsPointXY(2, 1), QgsPointXY(2, 0), QgsPointXY(3, 0)]
        )
        result = self.testClass.traceRouteGeom(QgsPointXY(0, 0), QgsPointXY(3, 0), testLineString2, tolerance)
        self.assertFalse(result)

        # checkRestrictionGeometryForTracedVertices
        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(3, 0)])
        result = self.testClass.checkRestrictionGeometryForTracedVertices(currGeom, testLineString1, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0, 2 0, 3 0)')

        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 1), QgsPointXY(2, 1), QgsPointXY(3, 0)])
        result = self.testClass.checkRestrictionGeometryForTracedVertices(currGeom, testLineString1, tolerance)
        self.assertFalse(result)

        testLineString3 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(2, 0), QgsPointXY(3, 0), QgsPointXY(4, 0)]
        )
        currGeom = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 1), QgsPointXY(2, 1), QgsPointXY(2, 0), QgsPointXY(4, 0)])
        result = self.testClass.checkRestrictionGeometryForTracedVertices(currGeom, testLineString3, tolerance)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 1, 2 1, 2 0, 3 0, 4 0)')

if __name__ == "__main__":
    suite = unittest.makeSuite(TOMsSnapTraceTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

