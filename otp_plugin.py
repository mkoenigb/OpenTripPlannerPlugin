# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenTripPlannerPlugin
                                 A QGIS plugin
 This plugin makes OpenTripPlanner functionalities accessible in QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-10-21
        git sha              : $Format:%H$
        copyright            : (C) 2019 - Today by Mario Königbauer
        email                : mkoenigb@gmx.de
        repository           : https://github.com/mkoenigb/OpenTripPlannerPlugin
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QObject, QThread, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from PyQt5.QtNetwork import  QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import *
from qgis.core import *
from qgis.utils import *


# Initialize Qt resources from file resources.py
from .resources import *
from .otp_plugin_worker_routes import *
from .otp_plugin_worker_isochrones import *
from .otp_plugin_general_functions import *
# Import the code for the dialog
from .otp_plugin_dialog import OpenTripPlannerPluginDialog
from osgeo import ogr
from datetime import *
import os
import urllib
import zipfile
import json

MESSAGE_CATEGORY = 'OpenTripPlanner PlugIn'

class OpenTripPlannerPlugin():
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
            'OpenTripPlannerPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&OpenTripPlanner Plugin')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('OpenTripPlannerPlugin', message)


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

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/otp_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'OpenTripPlanner Plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&OpenTripPlanner Plugin'),
                action)
            self.iface.removeToolBarIcon(action)

        
    def isochronesStartWorker(self): # method to start the worker thread
        isochrones_memorylayer_vl = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "Isochrones", "memory") # Create temporary polygon layer (output file)
        self.isochrones_thread = QThread()
        self.isochrones_worker = OpenTripPlannerPluginIsochronesWorker(self.dlg, self.iface, self.gf, isochrones_memorylayer_vl)
        # see https://realpython.com/python-pyqt-qthread/#using-qthread-to-prevent-freezing-guis
        # and https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html
        self.isochrones_worker.moveToThread(self.isochrones_thread) # move Worker-Class to a thread
        # Connect signals and slots:
        self.isochrones_thread.started.connect(self.isochrones_worker.run)
        self.isochrones_worker.isochrones_finished.connect(self.isochrones_thread.quit)
        self.isochrones_worker.isochrones_finished.connect(self.isochrones_worker.deleteLater)
        self.isochrones_thread.finished.connect(self.isochrones_thread.deleteLater)
        self.isochrones_worker.isochrones_progress.connect(self.isochronesReportProgress)
        self.isochrones_worker.isochrones_finished.connect(self.isochronesFinished)
        self.isochrones_thread.start() # finally start the thread
        # Disable/Enable GUI elements to prevent them from beeing used while worker threads are running and accidentially changing settings during progress
        self.gf.disableIsochronesGui() 
        self.gf.disableGeneralSettingsGui() 
        self.isochrones_thread.finished.connect(lambda: self.gf.enableIsochronesGui())
        self.isochrones_thread.finished.connect(lambda: self.gf.enableGeneralSettingsGui())
        
    def isochronesKillWorker(self): # method to kill/cancel the worker thread
        # print('pushed cancel') # debugging
        # see https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html
        try: # to prevent a Python error when the cancel button has been clicked but no thread is running use try/except
            self.isochrones_worker.stop() # call the stop method in worker class to break the work-loop so we can quit the thread
            if self.isochrones_thread.isRunning(): # check if a thread is running
                # print('pushed cancel, thread is running, trying to cancel') # debugging
                self.isochrones_thread.requestInterruption()
                self.isochrones_thread.exit() # Tells the thread’s event loop to exit with a return code.
                self.isochrones_thread.quit() # Tells the thread’s event loop to exit with return code 0 (success). Equivalent to calling exit (0).
                self.isochrones_thread.wait() # Blocks the thread until https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html#PySide6.QtCore.PySide6.QtCore.QThread.wait
        except:
            pass
       
    def isochronesReportProgress(self, n): # method to report the progress to gui
        self.dlg.Isochrones_ProgressBar.setValue(n) # set the current progress in progress bar

    def isochronesFinished(self, isochrones_resultlayer, isochrones_state, message=""): # method to interact with gui when thread is finished or canceled
        QgsProject.instance().addMapLayer(isochrones_resultlayer) # Show resultlayer in project
        # isochrones_state is indicating different states of the thread/result as integer
        if message:
            self.iface.messageBar().pushMessage("Warning", " Error occurred " + message, MESSAGE_CATEGORY, level=Qgis.Critical, duration=6)
        elif isochrones_state == 0:
            self.iface.messageBar().pushMessage("Warning", " Run-Method was never executed", MESSAGE_CATEGORY, level=Qgis.Critical, duration=6)
        elif isochrones_state == 1:
            self.iface.messageBar().pushMessage("Done!", " Isochrones job finished", MESSAGE_CATEGORY, level=Qgis.Success, duration=3)
        elif isochrones_state == 2:
            self.iface.messageBar().pushMessage("Done!", " Isochrones job canceled", MESSAGE_CATEGORY, level=Qgis.Success, duration=3)
        elif isochrones_state == 3:
            self.iface.messageBar().pushMessage("Warning", " No Isochrones to create - Check your settings and retry", MESSAGE_CATEGORY, level=Qgis.Warning, duration=6)
        else:
            self.iface.messageBar().pushMessage("Warning", " Unknown error occurred during execution", MESSAGE_CATEGORY, level=Qgis.Critical, duration=6)


    def routesStartWorker(self): # method to start the worker thread
        routes_memorylayer_vl = QgsVectorLayer("LineString?crs=epsg:4326", "Routes", "memory") # Create temporary polygon layer (output file)
        self.routes_thread = QThread()
        self.routes_worker = OpenTripPlannerPluginRoutesWorker(self.dlg, self.iface, self.gf, routes_memorylayer_vl)
        # see https://realpython.com/python-pyqt-qthread/#using-qthread-to-prevent-freezing-guis
        # and https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html
        self.routes_worker.moveToThread(self.routes_thread) # move Worker-Class to a thread
        # Connect signals and slots:
        self.routes_thread.started.connect(self.routes_worker.run)
        self.routes_worker.routes_finished.connect(self.routes_thread.quit)
        self.routes_worker.routes_finished.connect(self.routes_worker.deleteLater)
        self.routes_thread.finished.connect(self.routes_thread.deleteLater)
        self.routes_worker.routes_progress.connect(self.routesReportProgress)
        self.routes_worker.routes_finished.connect(self.routesFinished)
        self.routes_thread.start() # finally start the thread
        # Disable/Enable GUI elements to prevent them from beeing used while worker threads are running and accidentially changing settings during progress
        self.gf.disableRoutesGui()
        self.gf.disableGeneralSettingsGui()
        self.routes_thread.finished.connect(lambda: self.gf.enableRoutesGui())
        self.routes_thread.finished.connect(lambda: self.gf.enableGeneralSettingsGui())

    def routesKillWorker(self): # method to kill/cancel the worker thread
        # print('pushed cancel') # debugging
        # see https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html
        try: # to prevent a Python error when the cancel button has been clicked but no thread is running use try/except
            self.routes_worker.stop() # call the stop method in worker class to break the work-loop so we can quit the thread
            if self.routes_thread.isRunning(): # check if a thread is running
                # print('pushed cancel, thread is running, trying to cancel') # debugging
                self.routes_thread.requestInterruption()
                self.routes_thread.exit() # Tells the thread’s event loop to exit with a return code.
                self.routes_thread.quit() # Tells the thread’s event loop to exit with return code 0 (success). Equivalent to calling exit (0).
                self.routes_thread.wait() # Blocks the thread until https://doc.qt.io/qtforpython/PySide6/QtCore/QThread.html#PySide6.QtCore.PySide6.QtCore.QThread.wait
        except:
            pass
       
    def routesReportProgress(self, n): # method to report the progress to gui
        self.dlg.Routes_ProgressBar.setValue(n) # set the current progress in progress bar

    def routesFinished(self, routes_resultlayer, routes_state): # method to interact with gui when thread is finished or canceled
        QgsProject.instance().addMapLayer(routes_resultlayer) # Show resultlayer in project
        # routes_state is indicating different states of the thread/result as integer
        if routes_state == 0:
            self.iface.messageBar().pushMessage("Warning", " Run-Method was never executed", MESSAGE_CATEGORY, level=Qgis.Critical, duration=6)
        elif routes_state == 1:
            self.iface.messageBar().pushMessage("Done!", " Routes job finished", MESSAGE_CATEGORY, level=Qgis.Success, duration=3) 
        elif routes_state == 2:
            self.iface.messageBar().pushMessage("Done!", " Routes job canceled", MESSAGE_CATEGORY, level=Qgis.Success, duration=3) 
        elif routes_state == 3:
            self.iface.messageBar().pushMessage("Warning", " No Routes to create / no matching attributes - Check your settings and retry", MESSAGE_CATEGORY, level=Qgis.Warning, duration=6)
        elif routes_state == 4:
            self.iface.messageBar().pushMessage("Warning", " Inputlayer has no fields - Add at least a dummy-id field", MESSAGE_CATEGORY, level=Qgis.Warning, duration=6)        
        else:
            self.iface.messageBar().pushMessage("Warning", " Unknown error occurred during execution", MESSAGE_CATEGORY, level=Qgis.Critical, duration=6)
        
    def run(self):
        """Run method that performs all the real work"""
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = OpenTripPlannerPluginDialog()
            self.gf = OpenTripPlannerPluginGeneralFunctions(self.dlg, self.iface)
            # Calling maplayer selection on first startup to load layers into QgsMapLayerComboBox and initialize QgsOverrideButton stuff so selections can be done without actually using the QgsMapLayerComboBox (related to currentIndexChanged.connect(self.isochrones_maplayerselection) below) 
            self.gf.routes_maplayerselection()
            self.gf.isochrones_maplayerselection() 
            # Execute Main-Functions on Click: Placing them here prevents them from beeing executed multiple times, see https://gis.stackexchange.com/a/137161/107424
            self.dlg.Isochrones_RequestIsochrones.clicked.connect(lambda: self.isochronesStartWorker()) #Call the start worker method
            self.dlg.Isochrones_Cancel.clicked.connect(lambda: self.isochronesKillWorker())
            self.dlg.Routes_RequestRoutes.clicked.connect(lambda: self.routesStartWorker())
            self.dlg.Routes_Cancel.clicked.connect(lambda: self.routesKillWorker())
            
            # Calling Functions on button click
            self.dlg.GeneralSettings_CheckServerStatus.clicked.connect(self.gf.check_server_status)
            self.dlg.GeneralSettings_Save.clicked.connect(self.gf.store_general_variables) #Call store_general_variables function when clicking on save button
            self.dlg.GeneralSettings_Restore.clicked.connect(self.gf.restore_general_variables)
            self.dlg.Isochrones_SaveSettings.clicked.connect(self.gf.store_isochrone_variables)
            self.dlg.Isochrones_RestoreDefaultSettings.clicked.connect(self.gf.restore_isochrone_variables)
            self.dlg.Routes_SaveSettings.clicked.connect(self.gf.store_route_variables)
            self.dlg.Routes_RestoreDefaultSettings.clicked.connect(self.gf.restore_route_variables)
            
            # Calling Functions to update layer stuff when layerselection has changed
            self.dlg.Isochrones_SelectInputLayer.currentIndexChanged.connect(self.gf.isochrones_maplayerselection) # Call function isochrones_maplayerselection to update all selection related stuff when selection has been changed
            self.dlg.Routes_SelectInputLayer_Source.currentIndexChanged.connect(self.gf.routes_maplayerselection)
            self.dlg.Routes_SelectInputLayer_Target.currentIndexChanged.connect(self.gf.routes_maplayerselection)
            self.dlg.Routes_SelectInputField_Source.currentIndexChanged.connect(self.gf.routes_maplayerselection) # or "fieldChanged"?
            self.dlg.Routes_SelectInputField_Target.currentIndexChanged.connect(self.gf.routes_maplayerselection)
            self.dlg.Routes_DataDefinedLayer_Source.stateChanged.connect(self.gf.routes_maplayerselection)
            self.dlg.Routes_DataDefinedLayer_Target.stateChanged.connect(self.gf.routes_maplayerselection) 
            
        # Setting GUI stuff for startup every time the plugin is opened
        self.dlg.Isochrones_Date.setDateTime(QtCore.QDateTime.currentDateTime()) # Set Dateselection to today on restart or firststart, only functional if never used save settings, otherwise overwritten by read_route_variables()
        self.dlg.Routes_Date.setDateTime(QtCore.QDateTime.currentDateTime())
        self.dlg.Isochrones_ProgressBar.setValue(0) # Set Progressbar to 0 on restart or first start
        self.dlg.Routes_ProgressBar.setValue(0)
        self.dlg.GeneralSettings_ServerStatusResult.setText("Serverstatus Unknown")
        self.dlg.GeneralSettings_ServerStatusResult.setStyleSheet("background-color: white; color: black ")
        
        # Functions to execute every time the plugin is opened
        self.gf.read_general_variables() #Run Read-Stored-Variables-Function on every start
        self.gf.read_isochrone_variables()
        self.gf.read_route_variables()
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code. 
            QgsMessageLog.logMessage("OpenTripPlanner Plugin is already running! Close it before, if you wish to restart it.",MESSAGE_CATEGORY,Qgis.Warning)
            self.iface.messageBar().pushMessage("Error", "OpenTripPlanner Plugin is already running! Close it before, if you wish to restart it.",MESSAGE_CATEGORY,level=Qgis.Critical, duration=3)
