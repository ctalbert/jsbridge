from mozrunner.global_settings import *
import os

MOZILLA_PLUGINS = [os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                   'mozlab-current-0.1.9.2008050521.xpi')]

# MOZILLA_PREFERENCES = {'extensions.mozlab.mozrepl.port': 24242,
#                        'extensions.mozlab.mozrepl.autoStart': True}

MOZILLA_CMD_ARGS = ['-repl', '24242', '-jsconsole']

MOZILLA_CREATE_NEW_PROFILE = True

JSBRIDGE_START_FIREFOX = False

