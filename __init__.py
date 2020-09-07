# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenTripPlannerPlugin
                                 A QGIS plugin
 This plugin makes OpenTripPlanner functionalities accessible in QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-10-21
        copyright            : (C) 2019 by Mario Königbauer
        email                : mkoenigb@hm.edu
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
    """Load OpenTripPlannerPlugin class from file OpenTripPlannerPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .otp_plugin import OpenTripPlannerPlugin
    return OpenTripPlannerPlugin(iface)