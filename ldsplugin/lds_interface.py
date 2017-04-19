from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.wmts import WebMapTileService
from PyQt4.QtCore import QSettings

class LdsInterface():
    def __init__(self):
        self.api_key = self.get_api_key()
        
    def get_api_key(self):
        key = QSettings().value('ldsplugin/apikey') 
        if key:
            return key
        else: 
            return ''
    
    def update_api_key(self):
            self.api_key = self.get_api_key()
    
    def get_all_services(self):
        service_data = []
        for data in [self.get_wfs(), self.get_wms(), self.get_wmts()]:
            service_data.extend(data)
        return service_data
    
    def get_wfs(self):
        resp = self.request('WFS')
        return self.service_info(resp)
     
    def get_wmts(self):
        resp = self.request('WMTS')
        return self.service_info(resp)
    
    def get_wms(self):
        resp = self.request('WMS')
        return self.service_info(resp)
    
    def request(self, service):
        #try: 
        if service == 'WMS':
            return WebMapService('https://data.linz.govt.nz/services;key='+self.api_key+'/wms/', version='1.1.1')
        if service == 'WMTS':
            return WebMapTileService('https://data.linz.govt.nz/services;key='+self.api_key+'/wmts/1.0.0/WMTSCapabilities.xml', version='1.0.0')
        if service == 'WFS':
            return WebFeatureService('https://data.linz.govt.nz/services;key='+self.api_key+'/wfs/?service=WFS&request=GetCapabilities', version='1.1.0')
        #except:
        #    pass
            #how do I get at owslibs exceptions?
            
    def service_info(self, resp):
        service_data = []
        cont = (resp.contents)
        
        for c in cont:
            service_data.append([resp[c].id, resp.identification.type, resp[c].title, resp[c].abstract])
        return service_data
    