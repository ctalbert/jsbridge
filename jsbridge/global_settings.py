from mozrunner.global_settings import *
import os
import urllib

MOZILLA_PLUGINS = [os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                   'mozlab-current-0.1.9.2008050521.xpi'),
                   ]

basedir = os.path.abspath(os.path.dirname(__file__))

MOZILLA_PREFERENCES = {
    'extensions.mozlab.mozrepl.initUrl': 'file://'+urllib.pathname2url(os.path.join(basedir, 'customrepl.js')),
    }

MOZILLA_CMD_ARGS = ['-repl', '24242', '-jsconsole']

MOZILLA_CREATE_NEW_PROFILE = True

JSBRIDGE_START_FIREFOX = False

