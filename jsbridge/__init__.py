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

import sys
import optparse
import socket
import os
from time import sleep

import mozrunner
import simplesettings

import network
from jsobjects import JSObject
import global_settings

settings_env = 'JSBRIDGE_SETTINGS_FILE'

back_channel = None

def getBrowserWindow():
    return JSObject(network.bridge, "Components.classes['@mozilla.org/appshell/window-mediator;1'].getService(Components.interfaces.nsIWindowMediator).getMostRecentWindow('')")
    
def getPreferencesWindow():
    bridge = JSObject(network.bridge, "openPreferences()")
    sleep(1)
    return bridge
    
def ipython_shell(locals_dict):
    from IPython.Shell import IPShellEmbed
    ipshell = IPShellEmbed()
    ipshell(local_ns=locals_dict)
    
def code_shell(locals_dict):
    import code
    code.interact(local=locals_dict)    
    
def start_from_settings(settings, timeout=10):
    """Start the jsbridge from a setings dict"""
    if settings['JSBRIDGE_START_FIREFOX']:
        if not settings.has_key('JSBRIDGE_REPL_HOST'):
            settings['JSBRIDGE_REPL_HOST'] = 'localhost:24242'
        host, port = settings['JSBRIDGE_REPL_HOST'].split(':')
        port = int(port)
        moz = mozrunner.get_moz_from_settings(settings)
        moz.start()
        print 'Started ', moz.command
        settings['moz'] = moz
        ttl = 0
        while ttl < timeout:
            sleep(.25)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.close()
                break
            except socket.error:
                pass
    else:
        if not settings.has_key('JSBRIDGE_REPL_HOST'):
            settings['JSBRIDGE_REPL_HOST'] =  'localhost:4242'
        host, port = settings['JSBRIDGE_REPL_HOST'].split(':')
        port = int(port)
    
    network.create_network(host, port)
    browser_window = JSObject(network.bridge, "Components.classes['@mozilla.org/appshell/window-mediator;1'].getService(Components.interfaces.nsIWindowMediator).getMostRecentWindow('')")
    return browser_window


def set_debug(settings):
    
    module_path = global_settings.module_path   
    settings['MOZILLA_PLUGINS'] += [os.path.join(module_path, 'xpi',
                                        'javascript_debugger-0.9.87.4-fx+tb+sb+sm.xpi'),
                                    os.path.join(module_path, 'xpi', 'firebug-1.2.0b7-fx.xpi'),
                                    os.path.join(module_path, 'xpi', 'chromebug-trunk'),
                                    ]
    settings['MOZILLA_CMD_ARGS'] += ['-jsconsole', '-chrome', 
                                     'chrome://chromebug/content/chromebug.xul', 
                                     '-p', 'chromebug', '-firefox']
    rdf = open(os.path.join(module_path, 'xpi', 'chromebug-trunk', 'install.rdf.tpl.xml'), 'r').read()
    rdf = rdf.replace('@FULLVERSION@', '0.1')
    rdf = rdf.replace('<em:updateURL>@UPDATEPATH@/update.rdf</em:updateURL>\n', '')
    rdf = rdf.replace('<em:homepageURL>@UPDATEPATH@/index.html</em:homepageURL>\n', '')
    rdf = rdf.replace('<em:updateKey>ToBeReplaceByAValueFromMcCoy</em:updateKey>\n', '')
    f = open(os.path.join(module_path, 'xpi', 'chromebug-trunk', 'install.rdf'), 'w')
    f.write(rdf)
    f.close()
    return settings
    
def main():
    parser = optparse.OptionParser()
    parser.add_option("-s", "--settings", dest="settings",
                      help="Settings file for jsbridge.", metavar="JSBRIDGE_SETTINGS_FILE")
    parser.add_option("-b", "--binary", dest="binary",
                      help="Binary path.", metavar=None)
    parser.add_option("-d", "--default-profile", dest="default-profile",
                      help="Default profile path.", metavar=None)
    parser.add_option('-l', "--launch", dest="launch", action="store_true",
                      help="Launch a new firefox instance.", metavar=None)
    parser.add_option('-u', "--host", dest='host', 
                      help="The hostname:port pairing to connect to mozrepl.")
                      
    parser.add_option("-z", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Run with firebug, chromebug, venkman, and jsconsole")
    
    (options, args) = parser.parse_args()
    
    settings_path = getattr(options, 'settings', None)
    if settings_path is not None:
        settings_path = os.path.abspath(os.path.expanduser(settings_path))
        os.environ[settings_env] = settings_path
        
    settings = simplesettings.initialize_settings(global_settings, sys.modules[__name__],     
                                                  local_env_variable=settings_env)
    
    option_overrides = [('binary', 'MOZILLA_BINARY',),
                        ('profile', 'MOZILLA_PROFILE',),
                        ('default-profile', 'MOZILLA_DEFAULT_PROFILE',),
                        ('host', 'JSBRIDGE_REPL_HOST',),
                        ('launch', 'JSBRIDGE_START_FIREFOX',),
                       ]

    for opt, override in option_overrides:
        if getattr(options, opt, None) is not None:
            settings[override] = getattr(options, opt)
    
    if options.debug is True:
        set_debug(settings)    
        
    bridge = start_from_settings(settings)
    if settings.has_key('moz'):
        # We want the moz object in the local ns or the shell to access
        moz = settings['moz']
    
    try:
        import IPython
    except:
        IPython = None    
    if IPython is not None and '--usecode' not in sys.argv:
        sys.argv = sys.argv[:1]
        ipython_shell({'bridge':bridge, 'getBrowserWindow':getBrowserWindow, 'getPreferencesWindow':getPreferencesWindow})#locals())
    else:
        code_shell({'bridge':bridge, 'getBrowserWindow':getBrowserWindow, 'getPreferencesWindow':getPreferencesWindow})
    
    # # There is a bug in some of the traceback code IPython keeps around that causes a strange error here.
    # # The workaround is to remove it from sys.modules
    # x = sys.modules.pop('IPython', None)
    # if x is not None:
    #     del x
    
    if settings.has_key('moz'):
        moz.stop()
