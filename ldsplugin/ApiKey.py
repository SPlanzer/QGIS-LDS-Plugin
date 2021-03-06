from PyQt4.QtCore import QSettings

class ApiKey():
    def __init__(self):
        self.api_key = self.get_api_key()
    
    #TODO // change naming to Title case
    def get_api_key(self):
        key = QSettings().value('ldsplugin/apikey') 
        if not key:
            return ''
        return key
    
    def set_api_key(self, key):
        QSettings().setValue('ldsplugin/apikey', key)
        self.api_key = self.get_api_key()
