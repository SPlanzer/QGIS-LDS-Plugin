from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.wmts import WebMapTileService
from PyQt4.QtCore import QSettings

import re

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
       
    def get_service_data(self, service):
        resp = self.request(service)
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
            # standardise the different services string formatting
            cont_id = re.search(r'([aA-zZ]+\.[aA-zZ]+\.[aA-zZ]+\.[aA-zZ]+\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', resp[c].id)
            type = cont_id.group('type')
            id  =  cont_id.group('id')
            service_type = resp.identification.type.upper().strip('OGC:')
                        
            service_data.append([type, id, service_type, resp[c].title, resp[c].abstract])
        return service_data
    