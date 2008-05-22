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
import asynchat
import socket
import logging
import uuid
import copy
from time import sleep

import simplejson

logger = logging.getLogger(__name__)

class JavascriptException(Exception): pass

class Telnet(object, asyncore.dispatcher):
    def __init__(self, host, port):
        self.host, self.port = host, port
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.buffer = ''

    def handle_connect(self):
        logger.debug('Connected '+self.host+' on port '+str(self.port))
        
    def handle_close(self):
        logger.debug('Closed '+self.host+' on port '+str(self.port))

    def handle_expt(self): self.close() # connection failed, shutdown
    
    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def read_all(self):
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
        self.send('if ( this.jsbridgeRegisry == undefined ) { this.jsbridgeRegistry = {} }')

    def print_run(self, exec_string):
        rprint = self.back_channel.repl_name + '.print('
        call = 'try { ' + rprint + exec_string + ') } catch (err) { ' + rprint + '"#!EXCEPTION" + err) }' 
        result = self.raw_run(call)
        if result.startswith('#!EXCEPTION'):
            raise JavascriptException(result.replace('#!EXCEPTION',''))
        return result

    def raw_run(self, exec_string):
        rname = self.back_channel.repl_name
        block_uuid = str(uuid.uuid1())
        command = '%s.print("#!START_RAW_BLOCK::%s") ; %s ; %s.print("#!END_RAW_BLOCK::%s") ;' % (
                   rname, block_uuid, exec_string, rname, block_uuid
                   )
        response = []
        
        self.back_channel.block_callbacks[block_uuid] = lambda x: response.append(x)
        self.send(command)
        while len(response) is 0:
            sleep(.5)
        return response[0]
        
    run = print_run
        
class ReplBackChannel(Telnet):
    current_raw_block = None
    blocks = {}
    block_callbacks = {}
    finished_blocks = []
    trashes = []
    reading = False
    repl_name = None
    
    def block_finished(self, block_uuid):
        self.finished_blocks.append(block_uuid)
        self.block_callbacks.get(block_uuid, lambda x: None)(self.blocks[block_uuid])

    def read_callback(self, data):
        last_line = data.splitlines()[-1]
        self.repl_name = last_line.replace('> ','')
        self.repl_prompt = last_line
        self.read_callback = self.process_read

    def process_read(self, data):
        data = data.replace('\n'+self.repl_prompt+'\n', '').replace('\n'+self.repl_prompt, '')
        self.reading = True
        if self.current_raw_block is None:
            if '#!START_RAW_BLOCK::' not in data:
                self.trashes.append(data)
            else:
                lines = data.splitlines()
                start_index = lines.index([l for l in lines if '#!START_RAW_BLOCK::' in l][0])
                self.current_raw_block = lines[start_index].replace('#!START_RAW_BLOCK::', '')
                self.blocks[self.current_raw_block] = ''
                self.process_read('\n'.join(lines[start_index + 1:]))
        elif '#!END_RAW_BLOCK::' in data:
            lines = data.splitlines()
            end_index = lines.index([l for l in lines if '#!END_RAW_BLOCK::' in l][0])
            assert lines[end_index].replace('#!END_RAW_BLOCK::', '') == self.current_raw_block
            if len(lines) is not 1:
                self.blocks[self.current_raw_block] += '\n'.join(lines[:end_index ])
            else:
                if len(self.blocks[self.current_raw_block]) is 0:
                    self.blocks[self.current_raw_block] = None
                
            block_uuid = copy.copy(self.current_raw_block)
            self.current_raw_block = None
            self.reading = False
            self.block_finished(block_uuid)
            self.read_callback('\n'.join(lines[end_index:]))
        else:
            self.blocks[self.current_raw_block] += data
        self.reading = False
            

def create_network(hostname, port):
    back_channel = ReplBackChannel(hostname, port)
    repl = Repl(hostname, port, back_channel=back_channel)
    from threading import Thread
    thread = Thread(target=asyncore.loop)
    getattr(thread, 'setDaemon', lambda x : None)(True)
    thread.start()
    return back_channel, repl

