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
 *                                from owslib.wms import WebMapService                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt

from PyQt4.QtGui import QAction, QIcon, QSortFilterProxyModel, QHeaderView
from lds_tablemodel import LDSTableModel, LDSTableView
from lds_interface import LdsInterface

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from QgisLdsPlugin_dialog import QgisLdsPluginDialog
import os.path


#temp
from qgis.gui import QgsMessageBar


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
        self.menu = self.tr(u'&QGIS-LDS-Plugin')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QgisLdsPlugin')
        self.toolbar.setObjectName(u'QgisLdsPlugin')
        
        # Track data reading
        self.service_data = None
        
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
        self.dlg = QgisLdsPluginDialog()

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
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action
  
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QgisLdsPlugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Import LDS data'),
            callback=self.run,
            parent=self.iface.mainWindow())


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
        key = self.dlg.uTextAPIKey.text()
        if key:
            QSettings().setValue('ldsplugin/apikey', key) 
            self.lds_interface.update_api_key()
            self.setTableModelView()
        else:
            pass# TODO - RAISE ERROR "YOU DIDN'T WRITE ANYTHING!"
        
    def userSelection(self, selected):
        sourceIndex = self.proxy_model.mapToSource(selected)
        abstract = self.table_model.abstract(sourceIndex.row())
        self.dlg.uTextDescription.setText(abstract)
    
    def filterTable(self):
        filter_text = self.dlg.uTextFilter.text()
        self.proxy_model.setFilterKeyColumn(2)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterRegExp(filter_text)
    
    def TableModelView(self):
        # Set Table Model
        headers = ["id", "service", "layer", 'hidden']
        self.proxy_model = QSortFilterProxyModel()
        self.table_view = self.dlg.uDatasetsTableView
        self.table_model = LDSTableModel(self.service_data, headers)
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.setSortingEnabled(True)            
        
        # Trigger updating of data abstract on user selection
        selectionModel = self.table_view.selectionModel()
        selectionModel.currentRowChanged.connect(self.userSelection)
        
        # Table filtering trigger
        self.dlg.uTextFilter.textChanged.connect(self.filterTable)
        

    
    def setTableModelView(self):
        # Trigger the saving of api key
        self.dlg.uBtnSaveKey.pressed.connect(self.set_api_key)
        self.dlg.uTextAPIKey.setPlaceholderText(self.lds_interface.get_api_key())
        # Ensure an api key has been persisted 
        if not self.lds_interface.get_api_key():
            # if not, Have the users add the key
            # and do not attempt to make kds requests
            self.dlg.tabWidget.setCurrentIndex(1)
        else:
            # only request service data once
            if not self.service_data:
                try:
                    self.service_data = self.lds_interface.get_all_services()
                except:
                    self.iface.messageBar().pushMessage("Error", 
                                                   'LDS http request failed. Please check your API key', 
                                                   level=QgsMessageBar.CRITICAL)
                    return

            self.TableModelView()
        
    def run(self):
        """Run method that performs all the real work"""
        # Get table data
        
        self.setTableModelView()
        

        # show the dialog
        
        self.dlg.show()
        #TODO - Clear all selections in table view and text edit prior to opening
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

