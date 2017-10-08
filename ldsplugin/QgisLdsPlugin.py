"""
/***************************************************************************
 QgisLdsPlugin
                                 A QGIS plugin
 Import LDS OGC Datasets into QGIS
                              -------------------
        begin                : 2017-04-07
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Land Information New Zealand
        email                : splanzer@linz.govt.nz
 ***************************************************************************/
/***************************************************************************
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QListWidgetItem, QSortFilterProxyModel, QHeaderView, QMenu, QToolButton
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from lds_tablemodel import LDSTableModel, LDSTableView
from lds_interface import LdsInterface
from ApiKey import ApiKey
from Html import Html #poor name?
import re

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from gui.Service_dialog import ServiceDialog #TODO // standardise UI naming conventions
from gui.ApiKey_dialog  import ApiKeyDialog
from gui.Help_dialog  import HelpDialog

#from gui.Test import Test
import os.path


#temploadWMS
from qgis.gui import QgsMessageBar
from owslib import wfs, wms, wmts

# Dev only - debugging
try:
    import sys
    sys.path.append('/home/splanzer/.p2/pool/plugins/org.python.pydev_5.8.0.201706061859/pysrc')
    from pydevd import settrace, GetGlobalDebugger
except:
    pass

class QgisLdsPlugin:
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
        self.canvas = self.iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QgisLdsPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []

        self.toolbar = self.iface.addToolBar(u'QgisLdsPlugin')
        self.toolbar.setObjectName(u'QgisLdsPlugin')
#        self.popup_menu = QMenu(self.toolbar)
        
        self.tool_button = QToolButton()
        
        self.menu = self.tr(u'&QGIS-LDS-Plugin')
        # Track data reading
        self.wms_data = None
        self.wmts_data = None
        self.wfs_data = None
        self.row = None  
        self.service = None
        self.id = None
        self.service = None
        self.layer_title = None   
        # LDS request interface
        self.api_key = ApiKey()
        self.lds_interface = LdsInterface(self.api_key)
        
        self.version = {'wfs': '2.0.0', 'wms': '1.1.1' , 'wmts': '1.0.0'}
        
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
        return QCoreApplication.translate('QgisLdsPlugin', message)


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
        :type enabled_flag: boloadWMSol

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
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QgisLdsPlugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load LDS Data'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        self.service_dlg = ServiceDialog() # RENAME
        self.stacked_widget = self.service_dlg.qStackedWidget
        self.list_options = self.service_dlg.uListOptions
        self.list_options.itemClicked.connect(self.showSelectedOption)
        self.list_options.itemClicked.emit(self.list_options.item(0))
        self.warning = self.service_dlg.uLabelWarning
        
        self.warning.hide()
        # Change look of list widget
        self.list_options.setStyleSheet(
            """ QListWidget {
                    background-color: rgb(105, 105, 105);
                    outline: 0;
                }
                QListWidget::item {
                    color: white;
                    padding: 3px;
                }
                QListWidget::item::selected {
                    color: black;
                    background-color:palette(Window);
                    padding-right: 0px;
                };
            """
        )
                
        item = QListWidgetItem("ALL")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WFS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WMS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WMTS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)
        
        item = QListWidgetItem("Settings")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("About")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "OpenRaster.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)
    

#     def initGui(self):
#         """Create the menu entries and toolbar icons inside the QGIS GUI."""
#                 # Create the dialog (after translation) and keep reference
#         self.service_dlg = ServiceDialog()
# #         self.apikey_dlg = ApiKeyDialog()
# #         self.about_dlg = HelpDialog()
#     
#         """Create the menu entries and toolbar icons inside the QGIS GUI."""
# #         icon_path = ':/plugins/QgisLdsPlugin/icon.png'
# #         self.add_action(
# #             icon_path,
# #             text=self.tr(u'Road Maintenance'),
# #             callback=self.run,
# #             parent=iface.mainWindow())
# #         self.setupEnvironment()
#         
# #         self.apikey_dlg.buttonBox.accepted.connect(self.setApiKey)
#         
# #         icon_path = ':/plugins/QgisLdsPlugin/icon.png'
# #                 
# #         self.add_action = self.addAction(
# #             icon_path,
# #             text=self.tr(u'Load LDS Services'),
# #             callback=self.loadAllServices,
# #             parent=self.iface.mainWindow())
#         
# #         self.load_wmts = self.addAction(
# #             icon_path,
# #             text=self.tr(u'Load LDS WMTS'),
# #             callback=self.loadWMTS,
# #             parent=self.iface.mainWindow())
# # 
#         self.load_wms = self.addAction(
#             icon_path,
#             text=self.tr(u'Load LDS WMS'),
#             callback=self.loadWMS,
#             parent=self.iface.mainWindow())
# # 
# #         self.load_wfs = self.addAction(
# #             icon_path,
# #             text=self.tr(u'Load LDS WFS'),
# #             callback=self.loadWFS,
# #             parent=self.iface.mainWindow())
# 
# #         self.im_feeling_lucky = self.addAction(
# #             icon_path,
# #             text=self.tr(u"I'm feeling lucky"),
# #             callback=self.imFeelingLucky,
# #             parent=self.iface.mainWindow())
#         #         icon_path = ':/plugins/QgisLdsPlugin/icon.png'
# #         self.add_action(
# #             icon_path,
# #             text=self.tr(u'Road Maintenance'),
# #             callback=self.run,
# #             parent=iface.mainWindow())
# #         self.setupEnvironment()
# #         self.manage_api_key = self.addAction(
# #             icon_path,
# #             text=self.tr(u'Manage API Key'),
# #             callback=self.manageApi        icon_path = ':/plugins/roads/icons/roads_plugin.png'
# #Key,
# #             parent=self.iface.mainWindow())
# #         
# #         self.about = self.addActi    def initGui(self):
# 
# #             icon_path,
# #             text=self.tr(u'About'),
# #             callback=self.aboutShow,
# #             parent=self.iface.mainWindow())
#         
# #         for action in self.actions:
# #             self.popup_menu.addAction(action)
# #         
# #         self.tool_button.setMenu(self.popup_menu)
# #         self.tool_button.setDefaultAction(self.about)
# #         self.tool_button.setPopupMode(QToolButton.MenuButtonPopup)
# #         self.toolbar.addWidget( self.tool_button )
#         
        #set table model
        self.setTableModelView()
#         #set about html
# #         html = Html()
# #         self.about_dlg.uiHtmlDlg.setHtml(html.aboutHtml())
#         
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&QGIS-LDS-Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    
    def run(self):
        self.loadAllServices()
        
    def setApiKey(self):
        key = self.apikey_dlg.uTextAPIKey.text()
        self.api_key.set_api_key(key)
        self.lds_interface.keyChanged()
    
    def showSelectedOption(self, item):
        if item: # TO DO // WHY DO I GET NONE ON START UP
            if item.text() == 'ALL':
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WFS':
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WMTS':
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'Settings':
                self.stacked_widget.setCurrentIndex(1)
            elif item.text() == 'About':
                self.stacked_widget.setCurrentIndex(2)            
 
    def userSelection(self, selected):
        sourceIndex = self.proxy_model.mapToSource(selected)
        self.row = self.table_model.selectedRow(sourceIndex.row())
        abstract = self.row[4]
        self.service_type = self.row[0]
        self.id = self.row[1]
        self.service = self.row[2]
        self.layer_title = self.row[3]
        self.service_dlg.uTextDescription.setText(abstract)
    
    def filterTable(self):
        filter_text = self.service_dlg.uTextFilter.text()
        self.proxy_model.setFilterKeyColumn(3)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterRegExp(filter_text)
        
    def setTableModelView(self):
        # Set Table Model
        data = [['','','','']]
        
        headers = ['type','id', 'service', 'layer', 'hidden']
        self.proxy_model = QSortFilterProxyModel()
        self.table_view = self.service_dlg.uDatasetsTableView
        self.table_model = LDSTableModel(data, headers)
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)   
        self.table_view.horizontalHeader().setStretchLastSection(True)
        
        # Trigger updating of data abstract on user selection
        selectionModel = self.table_view.selectionModel()
        selectionModel.currentRowChanged.connect(self.userSelection)
        
        # Table filtering trigger
        self.service_dlg.uTextFilter.textChanged.connect(self.filterTable)
        
        # Import Button Clicked
        self.service_dlg.uBtnImport.clicked.connect(self.importDataset)

    def aboutShow(self):
        self.about_dlg.show()
    
    def errorDialog(self, error):
        self.iface.messageBar().pushMessage("Error", error, level=QgsMessageBar.CRITICAL)
    
    def requestServiceInfo(self, service):
        resp = self.lds_interface.getServiceData(service)
        if resp['err']:
            self.errorDialog(resp['err'])
        return resp['info']
    
    def loadAllServices(self):
        all_data = []
        all_services = {'wmts_data' : 'WMTS',
                        'wms_data' : 'WMS',
                         'wfs_data' : 'WFS'}
            
        for data, service in all_services.iteritems():
            if not getattr(self, data):
                service_data = self.requestServiceInfo(service)
            else: service_data = getattr(self, data)
            all_data.extend(service_data)
        self.dataToTable(all_data)
    
    def loadWMTS(self):        
        if not self.wmts_data:            
            self.wmts_data = self.requestServiceInfo('WMTS')
        if self.wmts_data:
            self.dataToTable(self.wmts_data)
    
    def loadWMS(self):
        if not self.wms_data:            
            self.wms_data = self.requestServiceInfo('WMS')
        if self.wms_data:
            self.dataToTable(self.wms_data)
    
    def loadWFS(self):
        if not self.wfs_data:            
            self.wfs_data = self.requestServiceInfo('WFS')
        if self.wfs_data:
            self.dataToTable(self.wfs_data)

    def dataToTable(self, table_data):
        self.table_model.setData(table_data)
        self.table_view.resizeColumnsToContents()   
        self.service_dlg.show() 
    
    def imFeelingLucky(self):
        pass
        # place holder - pop up "GO TO JAIL: Go directly to Jail. Do not pass Go. Do not collect $200"
        #OR "You Have won SECOND PRIZE in a BEAUTY CONTEST collect $10"
        # Community chest
        
        ''' IF DICTIONARY HAS SOME DATA MAKE SELECTION FROM THIS DATA.
        ELSE RANDOMLY SELECT A DATA TYPE AND ADD
        
        THEREFORE THREE METHODS.
        1/ HAS DATA
        2/ RANDOMLLY SELECT DATA TYPE
        3/ RANDOMLY SELECT LAYER
        '''
        
#     def manageApiKey(self):
#         curr_key = self.api_key.get_api_key()
#         if curr_key == '':
#             curr_key = 'No API Key stored. Please save a valid API Key'
#         self.apikey_dlg.uTextAPIKey.setPlaceholderText(curr_key)
#         self.apikey_dlg.show()

    def importDataset(self):
        # MVP read current map projection, make use of OTFP
        epsg = self.canvas.mapRenderer().destinationCrs().authid() 
        
        if self.service == "WFS":        
            url = ("https://data.linz.govt.nz/services;key={0}/{1}?SERVICE={1}&VERSION={2}&REQUEST=GetFeature&TYPENAME=data.linz.govt.nz:{3}-{4}").format(self.api_key.get_api_key(), self.service.lower(), self.version[self.service.lower()], self.service_type, self.id)
            layer = QgsVectorLayer(url,
                                  self.layer_title,
                                  self.service.upper())  
        
        elif self.service == "WMS":
            uri = "crs={0}&dpiMode=7&format=image/png&layers={1}-{2}&styles=&url=https://data.linz.govt.nz/services;key={3}/{4}/{1}-{2}?version={5}".format(epsg, self.service_type, self.id, self.api_key.get_api_key(), self.service.lower(), self.version[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                   'wms') 
        # need to understand more about param requirements here
        else:
            uri = "contextualWMSLegend=0&crs={0}&dpiMode=7&format=image/png&layers={1}-{2}&styles=style%3Dauto&tileMatrixSet={0}&url=https://data.linz.govt.nz/services;key={3}/{4}/{5}/{1}/{2}/WMTSCapabilities.xml".format(epsg, self.service_type, self.id, self.api_key.get_api_key(), self.service.lower(), self.version[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                   'wms')
                
        QgsMapLayerRegistry.instance().addMapLayer(layer) 
        self.service_dlg.close()
