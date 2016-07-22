# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CatchmentAnalyser
                                 A QGIS plugin
 Network based catchment analysis
                              -------------------
        begin                : 2016-05-19
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Laurens Versluis
        email                : l.versluis@spacesyntax.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Initialize Qt resources from file resources.py
import resources

# Import the code for the dialog
from catchment_analyser_dialog import CatchmentAnalyserDialog
import os.path

# Import QGIS classes
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

# Import tool classes
import catchment_tools

# Import utility tools
import utility_functions as uf

# Import the debug library
# set is_debug to False in release version
is_debug = False
try:
    import pydevd
    has_pydevd = False
except ImportError, e:
    has_pydevd = False
    is_debug = False

class CatchmentAnalyser:
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
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Initialize analysis
        self.catchmentAnalysis = catchment_tools.catchmentAnalysis(self.iface)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CatchmentAnalyser_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = CatchmentAnalyserDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Catchment Analyser')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CatchmentAnalyser')
        self.toolbar.setObjectName(u'CatchmentAnalyser')

        # Setup debugger
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=True)

        # Setup GUI signals
        self.dlg.networkCombo.activated.connect(self.updateCost)
        self.dlg.originsCombo.activated.connect(self.updateName)
        self.dlg.costCheck.stateChanged.connect(self.updateCost)
        self.dlg.nameCheck.stateChanged.connect(self.updateName)
        self.dlg.analysisButton.clicked.connect(self.runAnalysis)



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
        return QCoreApplication.translate('CatchmentAnalyser', message)

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
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CatchmentAnalyser/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Catchment Analyser'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Catchment Analyser'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def updateLayers(self):
        self.updateNetwork()
        self.updateOrigins()


    def updateNetwork(self):
        network_layers = uf.getLegendLayersNames(iface, geom=[1, ], provider='all')
        self.dlg.setNetworkLayers(network_layers)
        self.updateCost()


    def updateOrigins(self):
        origins_layers = uf.getLegendLayersNames(iface, geom=[0, ], provider='all')
        self.dlg.setOriginLayers(origins_layers)
        self.updateName()


    def updateCost(self):
        if self.dlg.costCheck.isChecked():
            network = self.getNetwork()
            self.dlg.setCostFields(uf.getNumericFieldNames(network))
        else:
            self.dlg.costCombo.clear()
            self.dlg.costCombo.setEnabled(False)


    def updateName(self):
        if self.dlg.nameCheck.isChecked():
            origins = self.getOrigins()
            self.dlg.setNameFields(uf.getFieldNames(origins))
        else:
            self.dlg.nameCombo.clear()
            self.dlg.nameCombo.setEnabled(False)


    def getNetwork(self):
        return uf.getLegendLayerByName(iface, self.dlg.getNetwork())


    def getOrigins(self):
        return uf.getLegendLayerByName(iface, self.dlg.getOrigins())


    def tempNetwork(self, epsg):
        if self.dlg.networkCheck.isChecked():
            output_network = uf.createTempLayer(
                'catchment_network',
                'LINESTRING',
                epsg,
                ['id',],
                [QVariant.Int,]
            )
            return output_network


    def tempPolygon(self, epsg):
        if self.dlg.polygonCheck.isChecked():
            output_polygon = uf.createTempLayer(
                'catchment_areas',
                'POLYGON',
                epsg,
                ['id', 'origin', 'distance'],
                [QVariant.Int, QVariant.Int, QVariant.Int]
            )
            return output_polygon

    def giveWarningMessage(self, message):
        # Gives warning according to message
        self.iface.messageBar().pushMessage(
            "Catchment Analyser: ",
            "%s" % (message),
            level=QgsMessageBar.WARNING,
            duration=5)

    def getAnalysisSettings(self):

        # Creating a combined settings dictionary
        settings = {}

        # Raise warnings
        if not self.getNetwork():
            self.giveWarningMessage("Catchment Analyser: No network selected!")
        elif self.getNetwork().crs().geographicFlag() or self.getOrigins().crs().geographicFlag():
            self.giveWarningMessage("Catchment Analyser: No projection found in input layers!")
        elif not self.getOrigins():
            self.giveWarningMessage("Catchment Analyser: No origins selected!")
        elif not self.dlg.getDistances():
            self.giveWarningMessage("Catchment Analyser: No distances defined!")
        else:
            # Get settings from the dialog
            settings['network'] = self.getNetwork()
            settings['cost'] = self.dlg.getCostField()
            settings['origins'] = self.getOrigins()
            settings['name'] = self.dlg.getName()
            settings['distances'] = self.dlg.getDistances()
            settings['network tolerance'] = self.dlg.getNetworkTolerance()
            settings['polygon tolerance'] = int(self.dlg.getPolygonTolerance())
            settings['crs'] = self.getNetwork().crs()
            settings['epsg'] = self.getNetwork().crs().authid()[5:] # removing EPSG:
            settings['temp network'] = self.tempNetwork(settings['epsg'])
            settings['temp polygon'] = self.tempPolygon(settings['epsg'])
            settings['output network'] = self.dlg.getNetworkOutput()
            settings['output polygon'] = self.dlg.getPolygonOutput()

            return settings


    def runAnalysis(self):
        self.dlg.analysisProgress.reset()
        if self.getAnalysisSettings():
            # Getting al the settings
            settings = self.getAnalysisSettings()
            self.dlg.analysisProgress.setValue(1)
            # Prepare the origins
            origins = self.catchmentAnalysis.origin_preparation(
                settings['origins'],
                settings['name']
            )
            self.dlg.analysisProgress.setValue(2)

            # Build the graph
            graph, tied_origins = self.catchmentAnalysis.graph_builder(
                settings['network'],
                settings['cost'],
                origins,
                settings['network tolerance'],
                settings['crs'],
                settings['epsg']
            )
            self.dlg.analysisProgress.setValue(3)

            # Run the analysis
            catchment_network, catchment_points = self.catchmentAnalysis.graph_analysis(
                graph,
                tied_origins,
                settings['distances']
            )
            self.dlg.analysisProgress.setValue(4)

            # Write and render the catchment polygons
            if self.dlg.polygonCheck.isChecked():
                output_polygon = self.catchmentAnalysis.polygon_writer(
                    catchment_points,
                    settings['distances'],
                    settings['temp polygon'],
                    settings['polygon tolerance']
                )
                if settings['output polygon']:
                    uf.createShapeFile(output_polygon, settings['output polygon'], settings['crs'])
                    output_polygon = QgsVectorLayer(settings['output polygon'], 'catchment_areas', 'ogr')
                    self.catchmentAnalysis.polygon_renderer(output_polygon)
                else:
                    self.catchmentAnalysis.polygon_renderer(output_polygon)
            self.dlg.analysisProgress.setValue(5)

            # Write and render the catchment network
            if self.dlg.networkCheck.isChecked():
                output_network = self.catchmentAnalysis.network_writer(
                    origins,
                    catchment_network,
                    settings['temp network']
                )
                if settings['output network']:
                    uf.createShapeFile(output_network, settings['output network'], settings['crs'])
                    output_network = QgsVectorLayer(settings['output network'], 'catchment_network', 'ogr')
                    self.catchmentAnalysis.network_renderer(output_network, settings['distances'])
                else:
                    self.catchmentAnalysis.network_renderer(output_network, settings['distances'])
            self.dlg.analysisProgress.setValue(6)

        # Closing the dialog
        self.dlg.closeDialog()


    def run(self):
        # Show the dialog
        self.dlg.show()

        # Update layers
        self.updateLayers()


