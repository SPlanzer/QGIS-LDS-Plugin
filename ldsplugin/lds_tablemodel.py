
#TODO Improve - namespace
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys


class LDSTableView(QTableView):
    
    """
    xxx    
    @param QTableView: Inherits from QtGui.QWidget
    @param QTableView: QtGui.QTableView()
    """
    
    # TODO // REMOVE
    
    #rowSelected = pyqtSignal( int, name="rowSelected" )
    #rowSelectionChanged = pyqtSignal( name="rowSelectionChanged" )
    #rowActivated = pyqtSignal( int, name="rowActivated" )
    
    def __init__( self, parent=None ):
        """ 
        Initialise  View for AIMS Queues
        """
        
        QTableView.__init__( self, parent )
        # Change default settings
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(17)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)



class LDSTableModel(QAbstractTableModel):

    def __init__(self, data = [[]], headers = [], parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = data
        self.header = headers

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])-1 # hiding description

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return unicode(self.arraydata[index.row()][index.column()])
    
    def setData(self, data):
        # not used for editing but refreshing all data in table
        self.layoutAboutToBeChanged.emit()
        self.arraydata = data
        self.layoutChanged.emit()
                
    def selectedRow(self, row):
        ''' 
        return the datasets abstract'''
        return self.arraydata[row]
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
    
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable #obviously not the final product

