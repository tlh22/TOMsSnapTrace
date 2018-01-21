# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TOMsSnapTrace
                                 A QGIS plugin
 snap and trace functions for TOMs
                             -------------------
        begin                : 2017-12-15
        copyright            : (C) 2017 by TH
        email                : th@mhtc.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TOMsSnapTrace class from file TOMsSnapTrace.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .TOMs_Snap_Trace import TOMsSnapTrace
    return TOMsSnapTrace(iface)
