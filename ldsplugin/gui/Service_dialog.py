#TODO// header


import os

from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Service_dialog_base.ui'))


class ServiceDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ServiceDialog, self).__init__(parent)
        self.setupUi(self)
