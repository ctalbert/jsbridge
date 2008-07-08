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

var EXPORTED_SYMBOLS = ["inspect", "getWindows"];

function getWindows(type) {
    if (type == undefined) {
        var type = "";
    }
    var windows = []
    var enumerator = Components.classes["@mozilla.org/appshell/window-mediator;1"]
                       .getService(Components.interfaces.nsIWindowMediator)
                       .getEnumerator(type);
    while(enumerator.hasMoreElements()) {
        windows = windows.concat(enumerator.getNext());
    }
    return windows;
}

function inspect(obj) {
// adapted from ddumpObject() at
// http://lxr.mozilla.org/mozilla/source/extensions/sroaming/resources/content/transfer/utility.js

    name = typeof(obj);

    var i = 0;
    objDesc = {"ptype":name};
    objDesc.props = [];
    for(var prop in obj) {
        var propDesc = {"name":prop};
        if(obj instanceof Components.interfaces.nsIDOMWindow &&
           (prop == 'java' || prop == 'sun' || prop == 'Packages')) {
            propDesc.result = false;
            propDesc.ptype = "object";
            propDesc.debug = "inspecting is dangerous =";
            // this.print(name + "." + prop + "=[not inspecting, dangerous]");
            continue;
        }

        try {
            i++;
            if(typeof(obj[prop]) == "object") {
                if(obj.length != undefined) {
                    propDesc.plength = obj[prop].length;
                    propDesc.ptype = "array";
                    // this.print(name + "." + prop + "=[probably array, length "
                    //            + obj[prop].length + "]");
                } else {
                    propDesc.ptype = "object";
                    // this.print(name + "." + prop + "=[" + typeof(obj[prop]) + "]");
                }
            } else if (typeof(obj[prop]) == "function") {
                propDesc.ptype = "function";
                // this.print(name + "." + prop + "=[function]");
            } else {
                propDesc.ptype = typeof(obj[prop]);
                propDesc.pvalue = obj[prop];
            }
                // this.print(name + "." + prop + "=" + obj[prop]);
            
            propDesc.doc = obj[prop].doc;
            // if(obj[prop] && obj[prop].doc && typeof(obj[prop].doc) == 'string')
                // propDesc.doc = obj[prop].doc;
                // this.print('    ' + obj[prop].doc);

        } catch(e) {
            propDesc.ptype = "object";
            propDesc.result = false;
            propDesc.debug = name + '.' + prop + ' - Exception while inspecting.';
            // this.print(name + '.' + prop + ' - Exception while inspecting.');
        }
        if (propDesc.result == undefined) {
            propDesc.result = true;
        }
        objDesc.props.push(propDesc);
    }
    if(!i) {
        propDesc.result = false;
        propDesc.debug = name + "is empty";
        // this.print(name + " is empty");   
    }
    return objDesc;
}