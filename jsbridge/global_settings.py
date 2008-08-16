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

from mozrunner.global_settings import *
import os
import urllib

module_path = os.path.abspath(os.path.dirname(__file__))

MOZILLA_PLUGINS = [os.path.join(module_path, 'extension'),
                   # os.path.join(module_path, 'xpi', 'mozlab-current-0.1.9.2008050521.xpi'),
                   ]

basedir = os.path.abspath(os.path.dirname(__file__))

MOZILLA_PREFERENCES = {
    # 'extensions.mozlab.mozrepl.initUrl': 'file://'+urllib.pathname2url(os.path.join(basedir, 'customrepl.js')),
    'extensions.chromebug.openalways' : True,
    'extensions.chromebug.showIntroduction' : False,
    'general.warnOnAboutConfig' : False,
    'extensions.venkman.enableChromeFilter' : False,
    }

MOZILLA_CMD_ARGS = ['-jsbridge', '24242', ]

MOZILLA_CREATE_NEW_PROFILE = True

JSBRIDGE_START_FIREFOX = False

