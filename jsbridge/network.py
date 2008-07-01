# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Corporation Code.
#
# The Initial Developer of the Original Code is
# Mikeal Rogers.
# Portions created by the Initial Developer are Copyright (C) 2008
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#  Mikeal Rogers <mikeal.rogers@gmail.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import asyncore
import socket
import logging
import uuid
import copy
from time import sleep

import simplejson

import callbacks

logger = logging.getLogger(__name__)

class JavascriptException(Exception): pass

class Telnet(object, asyncore.dispatcher):
    def __init__(self, host, port):
        self.host, self.port = host, port
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.buffer = ''
        self.logger = logger

    def __del__(self):
        self.close()

    def handle_connect(self):
        self.logger.debug('Connected '+self.host+' on port '+str(self.port))
        
    def handle_close(self):
        self.logger.debug('Closed '+self.host+' on port '+str(self.port))

    def handle_expt(self): self.close() # connection failed, shutdown
    
    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]
        
    def send(self, b):
        #print b
        asyncore.dispatcher.send(self, b)

    def read_all(self):
        import socket
        data = ''
        while 1:
            try:
                data += self.recv(4096)
            except socket.error:
                return data

    def handle_read(self):
        self.data = self.read_all()
        logger.debug('Raw RECV::'+self.data)
        self.read_callback(self.data)
        
    read_callback = lambda self, data: None
        
class Repl(Telnet):

    def __init__(self, *args, **kwargs):
        back_channel = kwargs.pop('back_channel')
        Telnet.__init__(self, *args, **kwargs)
        self.back_channel = back_channel
        sleep(.25)

    def repl_send(self, exec_string, callback_uuid=None):
        if uuid is None:
            callback_uuid = str(uuid.uuid1())
        call = ( 'jsbridge.controller.JSBridgeController.run('
            +simplejson.dumps(exec_string)+', '
            +self.back_channel.repl_name+', '
            +simplejson.dumps(callback_uuid)+');\n' 
                )
        self.send(call)
        return callback_uuid

    def run(self, exec_string):
        callback_uuid = str(uuid.uuid1())
        response = []
        callbacks.add_callback(lambda x: response.append(x), uuid=callback_uuid)
        self.repl_send(exec_string, callback_uuid)
        while len(response) is 0:
            sleep(.2)
        
        response = response[0]
        if response['exception'] is True:
            raise JavascriptException(response['result'])
        else:
            return response['result']
        
decoder = simplejson.JSONDecoder()

back_channel_on_connect_events = []
        
class ReplBackChannel(Telnet):
    trashes = []
    reading = False
    repl_name = None
    sbuffer = ''
    events_list = []

    def read_callback(self, data):
        #print data
        if len(data) > 0:
            last_line = data.splitlines()[-1]
            self.repl_name = last_line.replace('> ','')
            self.repl_prompt = last_line
            self.send("jsbridge.controller.JSBridgeController.addBridgeRepl("+self.repl_name+");\n")
            self.read_callback = self.process_read
            for event in set(back_channel_on_connect_events):
                self.add_bridge_listener(event)
            
    def add_bridge_listener(self, event):
        if event not in self.events_list:
            self.send("jsbridge.controller.JSBridgeController.addBridgeListener("+event+");\n")
        
    def fire_callbacks(self, obj):
        """Handle all callback fireing on json objects pulled from the data stream."""
        callbacks.fire_event(**dict([(str(key), value,) for key, value in obj.items()]))

    def process_read(self, data):
        """Parse out json objects and fire callbacks."""
        #print data
        self.sbuffer += data.replace('\n'+self.repl_prompt+'\n', '').replace('\n'+self.repl_prompt, '')
        self.reading = True
        self.parsing = True
        while self.parsing:
            # Remove erroneus data in front of callback object
            index = self.sbuffer.find('{')
            #print index
            if index is not -1 and index is not 0:
                self.sbuffer = self.sbuffer[index:]
            # Try to get a json object from the data stream    
            try:
                obj, index = decoder.raw_decode(self.sbuffer)
                #print 'passed'
            except Exception, e:
                self.parsing = False
                #print e.__class__, e.message
            # If we got an object fire the callback infra    
            if self.parsing:
                self.fire_callbacks(obj)
                self.sbuffer = self.sbuffer[index:]

def create_network(hostname, port):
    global back_channel, repl
    back_channel = ReplBackChannel(hostname, port)
    repl = Repl(hostname, port, back_channel=back_channel)
    from threading import Thread
    global thread
    thread = Thread(target=asyncore.loop)
    getattr(thread, 'setDaemon', lambda x : None)(True)
    thread.start()
    return back_channel, repl
