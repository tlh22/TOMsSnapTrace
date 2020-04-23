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
    QgsApplication, QgsRectangle, QgsPoint, QgsPointXY
)


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

    def testFindOverlap(self):

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

    def testReturnCorrectedGeometry(self):

        """

        2-+-+-+-+-1+-+-+-+-0+-+-+-+-3

        """


        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 1)]
        )

        # with no overlap
        result = self.testClass.checkLineForSelfOverlap(testLineString)
        self.assertFalse(result)
        #self.assertEqual(result.asWkt(), 'LineString (10 10, 20 10, 30 10)')
        print ('Test 2.2')

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0)]
        )
        # with overlap at start
        result = self.testClass.checkLineForSelfOverlap(testLineString)
        print (result)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0)')

        testLineString = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0), QgsPointXY(3, 0), QgsPointXY(2.5, 0), QgsPointXY(2, 0)]
        )
        # with overlap at start
        result = self.testClass.checkLineForSelfOverlap(testLineString)
        print (result)
        self.assertEqual(result.asWkt(), 'LineString (0 0, 1 0, 2 0)')

if __name__ == "__main__":
    suite = unittest.makeSuite(TOMsSnapTraceTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

