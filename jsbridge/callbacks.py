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

import network

uuid_callback_index = {}
event_callback_index = {}

def add_callback(callback, uuid=None, event=None):
    if uuid is not None:
        uuid_callback_index[uuid] = uuid_callback_index.get(uuid, []) + [callback]
    if event is not None:
        event_callback_index[event] = event_callback_index.get(event, []) [callback]    
        back_channel = getattr(network, 'back_channel', None)
        if back_channel is not None:
            back_channel.addBridgeListener(event)
        else:
            network.back_channel_on_connect_events.append(event)
    
def fire_event(eventType, uuid, result):
    event = eventType
    if uuid_callback_index.has_key(uuid):
        for callback in uuid_callback_index[uuid]:
            callback(result)
    if event_callback_index.has_key(event):
        for callback in event_callback_index[event]:
            callback(result)
