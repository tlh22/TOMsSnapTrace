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
    QgsApplication, QgsRectangle, QgsPoint
)

from qgis.analysis import (
    QgsVectorLayerDirector, QgsNetworkDistanceStrategy, QgsGraphBuilder, QgsGraphAnalyzer
)

from ..TOMs_Snap_Trace_dialog import TOMsSnapTraceDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class TOMsSnapTraceDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = TOMsSnapTraceDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""

        button = self.dialog.button_box.button(QDialogButtonBox.Ok)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Accepted)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        button = self.dialog.button_box.button(QDialogButtonBox.Cancel)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)

    def testFindOverlap(self):

        """

        2-+-+-+-+-1+-+-+-+-0+-+-+-+-3

        """


        polyline = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0)]
        )

        result = lineOverlaps(QgsPointXY(0, 0), QgsPointXY(-1, 0), QgsPointXY(-2, 0))
        self.assertfalse(result)

        result = lineOverlaps(QgsPointXY(-1, 0), QgsPointXY(-2, 0), QgsPointXY(1, 0))
        self.assertTrue(result)

if __name__ == "__main__":
    suite = unittest.makeSuite(TOMsSnapTraceDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

