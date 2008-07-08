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

var EXPORTED_SYMBOLS = ["JSBridgeController"];

var nativeJSON = Components.classes["@mozilla.org/dom/json;1"]
    .createInstance(Components.interfaces.nsIJSON);
    
var json2 = Components.utils.import("resource://jsbridge/modules/json2.js")

var jsonEncode = json2.JSON.stringify;

var uuidgen = Components.classes["@mozilla.org/uuid-generator;1"]
    .getService(Components.interfaces.nsIUUIDGenerator);

var hwindow = Components.classes["@mozilla.org/appshell/appShellService;1"]
         .getService(Components.interfaces.nsIAppShellService)
         .hiddenDOMWindow;

function range(begin, end) {
  for (let i = begin; i < end; ++i) {
    yield i;
  }
}

var JSBridgeController = {"methodDispatches":{}};

JSBridgeController.registry = {};
JSBridgeController.eventsByUUID = {};
JSBridgeController.eventsByType = {};
JSBridgeController.callbackRegistryByUUID = {};
JSBridgeController.callbackRegistryByType = {};
JSBridgeController.bridgeRepl = [];

JSBridgeController.fireEvent = function (eventType, obj, uuid, repl) {
    if (uuid == undefined) {
        uuid = uuidgen.generateUUID().toString();
        }
    JSBridgeController.eventsByUUID[uuid] = {"eventType":eventType, "obj":obj};
    if (JSBridgeController.eventsByType[eventType] == undefined) {
        JSBridgeController.eventsByType[eventType] = [];
    }
    JSBridgeController.eventsByType[eventType] = JSBridgeController.eventsByType[eventType].concat({"uuid":uuid, "obj":obj});
    JSBridgeController.fireCallbacks(eventType, obj, uuid, repl);
}

JSBridgeController.fireCallbacks = function (eventType, obj, uuid, repl) {
    // var x = {"eventType":eventType, "result":obj, "uuid":uuid};
    if (JSBridgeController.callbackRegistryByUUID[uuid] != undefined) {
        JSBridgeController.callbackRegistryByUUID[uuid](eventType, obj, uuid);
    }
    if (JSBridgeController.callbackRegistryByType[eventType] != undefined) {
        for ( var i=0, len=JSBridgeController.callbackRegistryByType[eventType].length; i<len; ++i ){
          JSBridgeController.callbackRegistryByType[eventType][i](eventType, obj, uuid);
        }
    }
}

JSBridgeController.addListener = function (eventType, callback) {
    var listner = function (eventType, obj, uuid) { return callback(obj); }
    
    if (JSBridgeController.callbackRegistryByType[eventType] != undefined) {
        JSBridgeController.callbackRegistryByType[eventType] = JSBridgeController.callbackRegistryByType[eventType].concat(listener);
    }
    else {
        JSBridgeController.callbackRegistryByType[eventType] = [listener];
    }
}

JSBridgeController.bridgeListener = function (eventType, obj, uuid) {
    for ( var i=0, len=JSBridgeController.bridgeRepl.length; i<len; ++i ){
        JSBridgeController.bridgeRepl[i].onOutput(jsonEncode({"eventType":eventType, "result":obj, "uuid":uuid}));
    }
}

JSBridgeController.addBridgeListener = function (eventType) {
    if (JSBridgeController.callbackRegistryByType[eventType] != undefined) {
        JSBridgeController.callbackRegistryByType[eventType] = JSBridgeController.callbackRegistryByType[eventType].concat(JSBridgeController.bridgeListener);
    }
    else {
        JSBridgeController.callbackRegistryByType[eventType] = [JSBridgeController.bridgeListener];
    }
} 

JSBridgeController.addBridgeRepl = function (repl) {
    JSBridgeController.bridgeRepl = JSBridgeController.bridgeRepl.concat(repl);
}

JSBridgeController.wrapDispatch = function (uuid) {
    var dispatch = JSBridgeController.methodDispatches[uuid];
    // dispatch.repl.print("test1")
    if ( dispatch.method != undefined ) {
        eventType = "functionCall";
        dispatch.exec_string = dispatch.method + "(" + 
            ["dispatch.args["+i+"]" for each (i in range(0, dispatch.args.length))]
            .join(', ') + ")";
        }
    else {
        eventType = "execString";
    }
    
    try {
        dispatch.result = hwindow.eval(dispatch.exec_string);
        dispatch.exception = false;
    } catch(e) {
        dispatch.result = e;
        dispatch.exception = true;
    }
    if (dispatch.result == undefined) {
        dispatch.result = null;
    }

    repl = dispatch.repl;
    uuid = dispatch.uuid;
    delete dispatch.repl;
    delete dispatch.uuid;
    // repl.onOutput(nativeJSON.encode(dispatch));
    // repl.onOutput(jsonEncode(dispatch));
    JSBridgeController.fireEvent(eventType, dispatch, uuid, repl);
}

JSBridgeController.run_method = function (method, args, repl, uuid) {
    if (uuid == undefined) {
        uuid = uuidgen.generateUUID().toString();
        }
        
    var listener = function (eventType, obj, uuid) { 
        repl.onOutput(jsonEncode({"eventType":eventType, "result":obj, "uuid":uuid}));
    }

    JSBridgeController.callbackRegistryByUUID[uuid] = listener;    
    JSBridgeController.methodDispatches[uuid] = {"method":method, "args":args, "repl":repl, "uuid":uuid};
    
    hwindow.setTimeout("jsbridge.controller.JSBridgeController.wrapDispatch('"+uuid+"')", 1 );
    return uuid;
}

JSBridgeController.run = function (exec_string, repl, uuid) {
    if (uuid == undefined) {
        uuid = uuidgen.generateUUID().toString();
        }
    
    var listener = function (eventType, obj, auuid) { 
        repl.onOutput(jsonEncode({"eventType":eventType, "result":obj, "uuid":auuid}));
    }
    
    JSBridgeController.callbackRegistryByUUID[uuid] = listener;    
    JSBridgeController.methodDispatches[uuid] = {"exec_string":exec_string, "repl":repl, "uuid":uuid};

    hwindow.setTimeout("jsbridge.controller.JSBridgeController.wrapDispatch('"+uuid+"')", 1 );

    return uuid;
}

// var window = Components.classes["@mozilla.org/appshell/appShellService;1"]
//          .getService(Components.interfaces.nsIAppShellService)
//          .hiddenDOMWindow;
// 
// window.Application.events.addListener("xul-window-visible", function (w) { JSBridgeController.bridgeRepl[0].onOutput('\nasdf\n') });

