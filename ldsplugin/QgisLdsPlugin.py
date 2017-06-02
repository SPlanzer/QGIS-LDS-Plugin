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
from PyQt4.QtGui import QAction, QIcon, QSortFilterProxyModel, QHeaderView, QMenu, QToolButton
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsMapLayerRegistry
from lds_tablemodel import LDSTableModel, LDSTableView
from lds_interface import LdsInterface
import re #temp

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from gui.Service_dialog import ServiceDialog #TODO // standardise UI naming conventions
from gui.ApiKey_dialog  import ApiKeyDialog
#from gui.Test import Test
import os.path


#temp
from qgis.gui import QgsMessageBar

# Dev only - debugging
try:
    import sys
    sys.path.append('/opt/eclipse/plugins/org.python.pydev_4.4.0.201510052309/pysrc')
    from pydevd import settrace, GetGlobalDebugger
    settrace()
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
        self.popup_menu = QMenu(self.toolbar)
        
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
        self.lds_interface = LdsInterface()
        
        
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


    def addAction(
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
        :type callback: functionApiKey_dialog
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. DefaulApiKey_dialogts to True.
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
        :rtypeQmenu: QAction
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        #tool_button_menu,addAction(action)
        
        self.actions.append(action)
        return action
    
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
                # Create the dialog (after translation) and keep reference
        self.service_dlg = ServiceDialog()
        self.apikey_dlg = ApiKeyDialog()
        
        self.apikey_dlg.buttonBox.accepted.connect(self.set_api_key)
        
        icon_path = ':/plugins/QgisLdsPlugin/icon.png' # can do a much better job using dir+
        self.load_all = self.addAction(
            icon_path,
            text=self.tr(u'Load All LDS Services'),
            callback=self.loadAllServices,
            parent=self.iface.mainWindow())
        
        self.load_wmts = self.addAction(
            icon_path,
            text=self.tr(u'Load LDS WMTS'),
            callback=self.loadWMTS,
            parent=self.iface.mainWindow())

        self.load_wms = self.addAction(
            icon_path,
            text=self.tr(u'Load LDS WMS'),
            callback=self.loadWMS,
            parent=self.iface.mainWindow())

        self.load_wfs = self.addAction(
            icon_path,
            text=self.tr(u'Load LDS WFS'),
            callback=self.loadWFS,
            parent=self.iface.mainWindow())

        self.im_feeling_lucky = self.addAction(
            icon_path,
            text=self.tr(u"I'm feeling lucky"),
            callback=self.imFeelingLucky,
            parent=self.iface.mainWindow())
        
        self.manage_api_key = self.addAction(
            icon_path,
            text=self.tr(u'Manage API Key'),
            callback=self.manageApiKey,
            parent=self.iface.mainWindow())
        
        for action in self.actions:
            self.popup_menu.addAction(action)
        
        self.tool_button.setMenu(self.popup_menu)
        self.tool_button.setDefaultAction(self.load_all)
        self.tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolbar.addWidget( self.tool_button )
        
        #set table model
        self.setTableModelView()
        
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&QGIS-LDS-Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    
    def set_api_key(self):
        key = self.apikey_dlg.uTextAPIKey.text()
        QSettings().setValue('ldsplugin/apikey', key) 
        self.lds_interface.update_api_key()
        
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
        data = [['g','h','j','k']]
        
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

        
    def loadAllServices(self):
        all_data = []
        all_services = {'wmts_data' : 'WMTS',
                        'wms_data' : 'WMS',
                        'wfs_data' : 'WFS'}
            
        for data, service in all_services.iteritems():
            if not getattr(self, data):
                service_data = self.lds_interface.get_service_data(service)
                setattr(self, data, service_data)
            else: service_data = getattr(self, data)
            all_data.extend(service_data)
        self.dataToTable(all_data)
    
    def loadWMTS(self):
        if not self.wmts_data:
            self.wmts_data = self.lds_interface.get_service_data('WMTS')
        self.dataToTable(self.wmts_data)
    
    def loadWMS(self):
        if not self.wms_data:
            self.wms_data =  self.lds_interface.get_service_data('WMS')
        self.dataToTable(self.wms_data)
    
    def loadWFS(self):
        if not self.wfs_data:
            self.wfs_data = self.lds_interface.get_service_data('WFS')
        self.dataToTable(self.wfs_data)
    
    def dataToTable(self, table_data):
        self.table_model.setData(table_data)
        self.table_view.resizeColumnsToContents()   
        self.service_dlg.show() 
    
    def imFeelingLucky(self):
        pass
    
    def manageApiKey(self):
        self.apikey_dlg.show()

    def importDataset(self):
        # 1. IS raster or vector 
        # format url    
        # check a selection has been made
        # close dlg     
        # zoom to layer
        key = '0aab3b43c5b340e096fbbb0ffc52c784'
        
        

        if self.service == "WFS":
            version = '1.0.0' 
        else:
            version = '1.1.1'
        #url = ("https://data.linz.govt.nz/services;key={0}/{1}/{2}?SERVICE={3}&VERSION={4}&REQUEST=GetMap&typename=data.linz.govt.nz:{2}").format(key, service.lower(), id, service.upper(), version )
        
        #url = ("https://data.linz.govt.nz/services;key={0}/{1}?SERVICE={3}&VERSION={4}&REQUEST=GetFeature&srsname=EPSG:2193&typeNames={5}-{2}").format(key, self.service.lower(), self.id, self.service.upper(), version, self.service_type, )
        url = ("https://data.linz.govt.nz/services;key={0}/{1}?SERVICE={3}&VERSION={4}&REQUEST=GetFeature&typeNames={5}-{2}").format(key, self.service.lower(), self.id, self.service.upper(), version, self.service_type, )
       
       #https://data.linz.govt.nz/services;key=0aab3b43c5b340e096fbbb0ffc52c784/wms?service=WMS&version=1.1.1&request=GetMap&layers=layer-2087
       url = 
      
        self.iface.addVectorLayer(url,
                                  self.layer_title,
                                  self.service.upper())   
        self.service_dlg.close()
        
    
