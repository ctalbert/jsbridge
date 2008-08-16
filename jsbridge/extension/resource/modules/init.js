// ***** BEGIN LICENSE BLOCK *****
// Version: MPL 1.1/GPL 2.0/LGPL 2.1
// 
// The contents of this file are subject to the Mozilla Public License Version
// 1.1 (the "License"); you may not use this file except in compliance with
// the License. You may obtain a copy of the License at
// http://www.mozilla.org/MPL/
// 
// Software distributed under the License is distributed on an "AS IS" basis,
// WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
// for the specific language governing rights and limitations under the
// License.
// 
// The Original Code is Mozilla Corporation Code.
// 
// The Initial Developer of the Original Code is
// Mikeal Rogers.
// Portions created by the Initial Developer are Copyright (C) 2008
// the Initial Developer. All Rights Reserved.
// 
// Contributor(s):
//  Mikeal Rogers <mikeal.rogers@gmail.com>
// 
// Alternatively, the contents of this file may be used under the terms of
// either the GNU General Public License Version 2 or later (the "GPL"), or
// the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
// in which case the provisions of the GPL or the LGPL are applicable instead
// of those above. If you wish to allow use of your version of this file only
// under the terms of either the GPL or the LGPL, and not to allow others to
// use your version of this file under the terms of the MPL, indicate your
// decision by deleting the provisions above and replace them with the notice
// and other provisions required by the GPL or the LGPL. If you do not delete
// the provisions above, a recipient may use your version of this file under
// the terms of any one of the MPL, the GPL or the LGPL.
// 
// ***** END LICENSE BLOCK *****

var EXPORTED_SYMBOLS = ["jsbridge"];

var hwindow = Components.classes["@mozilla.org/appshell/appShellService;1"]
         .getService(Components.interfaces.nsIAppShellService)
         .hiddenDOMWindow;

jsbridge = {
    controller: Components.utils.import('resource://jsbridge/modules/controller.js'),
    debugging:  Components.utils.import('resource://jsbridge/modules/debugging.js'),
    events:     Components.utils.import('resource://jsbridge/modules/events.js'),
    utils:      Components.utils.import('resource://jsbridge/modules/utils.js'),
}
jsbridge.controller.JSBridgeController.jsbridge = jsbridge;

function printEvent (item) {
    jsbridge.controller.JSBridgeController.bridgeRepl[0].print(item.topic);
}

// jsbridge.events.addListener('domwindowopened', printEvent);
// jsbridge.events.addListener('toplevel-window-ready', printEvent);
// jsbridge.events.addListener('xul-window-registered', printEvent);
// jsbridge.events.addListener('xul-window-visible', printEvent);
// jsbridge.events.addListener('xul-window-destroyed', printEvent);
// jsbridge.events.addListener('dom-window-destroyed', printEvent);


function attachToNewWindow (item) {
    item.subject.jsbridge = jsbridge;
    item.subject._hwindow = hwindow;
}

jsbridge.events.addListener('domwindowopened', attachToNewWindow);

hwindow.jsbridge = jsbridge;

var enumerator = Components.classes["@mozilla.org/appshell/window-mediator;1"]
                   .getService(Components.interfaces.nsIWindowMediator)
                   .getEnumerator("");
while(enumerator.hasMoreElements()) {
    var win = enumerator.getNext();
    attachToNewWindow({"subject":win});
}

function attachDebuggingToVenkman (item) {
    // jsbridge.controller.JSBridgeController.bridgeRepl[0].print('here '+typeof(item.subject.print))
    function attach() {
        // jsbridge.controller.JSBridgeController.bridgeRepl[0].print(
        //     jsbridge.controller.jsonEncode([prop for (prop in item.subject)])
        // );
        if (item.subject.display != undefined) {
            item.subject.inspect = jsbridge.debugging.dinspect;
            hwindow.venkmanDisplay = item.subject.display;
        }
    }
    
    item.subject.addEventListener("load", attach, false) 
}


jsbridge.events.addListener('toplevel-window-ready', attachDebuggingToVenkman);

jsbridge.server = {}; 
Components.utils.import('resource://jsbridge/modules/server.js', jsbridge.server);
// 
// var mediator = Components.classes['@mozilla.org/appshell/window-mediator;1']
//          .getService(Components.interfaces.nsIWindowMediator)
// 
// for (i in hwindow.Application.windows) {
//     if (hwindow.Application.windows[i]._window != undefined) {
//         hwindow.Application.windows[i]._window.jsbridge = jsbridge;
//     }
// }

// Components.utils.import('resource://jsbridge/modules/controller.js').JSBridgeController.test = 'working'
