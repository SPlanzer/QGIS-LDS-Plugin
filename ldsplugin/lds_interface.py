from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.wmts import WebMapTileService
from PyQt4.QtCore import QSettings

import re

class LdsInterface():
    def __init__(self, api_key_instance):
        self.api_key_instance = api_key_instance
        self.key = self.api_key_instance.get_api_key()
        self.resp = {}
    
    def keyChanged(self):
        self.key = self.api_key_instance.get_api_key()
    
    def hasKey(self):
        if not self.key:
            return False
        return True
      
    def getServiceData(self, service):
        self.resp = {'err' : None,
                     'resp': None,
                     'info': None}
        
        # Ensure an API Key has been stored
        if not self.hasKey():
            self.resp['err'] = "Missing API Key. Please supply an LDS API key (plugin's menu > API Key)"
            return self.resp
        
        # TODO // GET SO MANT TIMEOUTS. must habdle these
        
        # Request - Get Info for the service
        self.request(service)
        if self.resp['err']:
            return self.resp
        
        # Format the response data
        self.service_info()
        
        return self.resp
        
    
    def request(self, service):

        try: 
            if service == 'WMS':
                self.resp['resp'] = WebMapService('https://data.linz.govt.nz/services;key='+self.key+'/wms/', version='1.1.1')
                return
            if service == 'WMTS':
                self.resp['resp'] = WebMapTileService('https://data.linz.govt.nz/services;key='+self.key+'/wmts/1.0.0/WMTSCapabilities.xml?count=10', version='1.0.0')
                return
                #return WebMapTileService('https://data.linz.govt.nz/services;key='+self.key+'/wmts/1.0.0/layer/1455/WMTSCapabilities.xml?count=10', version='1.0.0')
            if service == 'WFS':
                self.resp['resp'] = WebFeatureService('https://data.linz.govt.nz/services;key='+self.key+'/wfs/?service=WFS&request=GetCapabilities', version='1.1.0')
                return
        
        except:
            resp['err'] = "Something went wrong with the request. Timeout??? wrong key ???"
        #    pass
            #how do I get at owslibs exceptions?
                        
    def service_info(self):
        service_data = []
        resp = self.resp['resp']
        cont = (resp.contents)
        
        for c in cont:
            # standardise the different services string formatting
            cont_id = re.search(r'([aA-zZ]+\.[aA-zZ]+\.[aA-zZ]+\.[aA-zZ]+\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', resp[c].id)
            type = cont_id.group('type')
            id  =  cont_id.group('id')
            service_type = resp.identification.type.upper().strip('OGC:').strip(' ')
                        
            service_data.append([type, id, service_type, resp[c].title, resp[c].abstract])
        
        self.resp['info'] = service_data
    
    
    