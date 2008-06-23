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

import simplejson
import uuid 

# def parse_inspection(body):
#     """Parse the repl.inspect() text to a dict and figure out javascript object type."""
#     obj_type = body[1:body.find('>')]
#     parsed = dict( [ l.replace('<'+obj_type+'>.', '').split('=', 1) for l in body.splitlines() if '=' in l ] )
#     parsed['__doc__'] = parsed.get('doc')
#     return parsed, obj_type

def parse_inspection(obj):
    obj_type = obj["ptype"]
    props = obj["props"]
    return props, obj_type

# def guess_transform(repl, basename, name, value):
#     """Guess the JSObject which should be returned for a given value."""
#     if value is None:
#         return None
#         
#     fullname = basename + '.' + name
#     
#     if value == '[object]':
#         return JSObject(repl, fullname)
#     if value == '[function]':
#         return JSFunction(repl, fullname)
#     if value.startswith('['):
#         return JSObject(repl, fullname)
# 
#     # Brute Force object creation
#     try:
#         val = simplejson.loads(value)
#         return init_jsobject(py_type_cases[type(val)], repl, fullname, value)
#     except: pass
#     
#     return init_jsobject(JSString, repl, fullname, value)

def create_jsobject_dict(repl, basename, props):
    """Create a dict of jsobjects for a given inspect dict. Guesses transform for each object."""
    prop_dict = {}
    for prop in props:
        if prop['result'] is True:
            prop_dict[prop['name']] = create_jsobject(repl, basename+'.'+prop['name'], prop.get('pvalue', None), prop['ptype'])

    return prop_dict

def guess_serialization(arg):
    """Guess the serialization of a given Python object to a javascript textual representaion (JSON)"""
    if isinstance(arg, JSObject):
        return arg._name_
    else:
        return simplejson.dumps(arg)

def create_jsobject(repl, fullname, value, obj_type=None):
    """Create a single JSObject for named object on other side of the bridge.
    
    Handles various initization cases for different JSObjects."""
    if obj_type is None:
        obj_type = repl.run('typeof('+fullname+')')
        
    if value is True or value is False:
        return value

    if js_type_cases.has_key(obj_type):
        cls, needs_init = js_type_cases[obj_type]
        # Objects that requires initialization are base types that have "values".
        if needs_init:
            obj = init_jsobject(cls, repl, fullname, value)
        else:
            obj = cls(repl, fullname)
        return obj
    else:
        # Something very bad happened, we don't have a representation for the given type.
        raise TypeError("Don't have a JSObject for javascript type "+obj_type)

def get_setattr_call(basename, name, value):
    """Create the javascript call for a Python __setattr__ event."""
    return basename + '.' + name, guess_serialization(value) 

def get_setitem_call(basename, name, value):
    """Create the javascript call for a Python __setitem__ event."""
    return basename + '[' + name + ' ]',  guess_serialization(value)

def get_function_call(basename, args):
    """Create the javascript call for a Python function call."""
    fuuid = str(uuid.uuid1()).replace('-','')
    return fuuid, basename + '(' + ', '.join([guess_serialization(arg) for arg in args]) + ')' 

def get_getitem_call(basename, name):
    """Create the javascript call for a Python __getitem__ event."""
    return basename + '[' + guess_serialization(name) + ']'
    
class JSObject(object):
    """Base javascript object representation."""
    _loaded_ = False
    
    def __init__(self, repl, name, *args, **kwargs):
        self._repl_ = repl
        self._name_ = name
    
    def __jsget__(self, call):
        """Abstraction for final step in get events; __getitem__ and __getattr__.
        
        Handles execution of javascript call and returns JSObject instance."""
        result = self._repl_.run(call)
        
        if type(result) is str:
            result = create_jsobject(self._repl_, call, result)
        return result
    
    def __getattr__(self, name):
        """Get the object from jsbridge. 
        
        Handles lazy loading of all attributes of self."""
        # Lazy load all the objects from the jsbridge once gettattr gets called.
        if self._loaded_ is False and not ( name.startswith('__') and name.endswith('__') ):
            self._load()
        # A little hack so that ipython returns all the names _after_ loading.
        if name == '_getAttributeNames':
            return lambda : dir(self)
        result = self.__dict__.get(name)
        if result is None:
            # According to the Python special class methods specification, __getattr__ failures
            # should raise attribute error when no attribute is found, returning None causes big 
            # problems.
            raise AttributeError(self._name_+' has not attribute '+name)
        else:
            return result
    
    def __getitem__(self, name):
        return self.__jsget__(get_getitem_call(self._name_, name))
        
    def __setattr__(self, name, value):
        """Set the given JSObject as an attribute of this JSObject and make proper javascript
        assignment on the other side of the bridge."""
        if name.startswith('_') and name.endswith('_'):
            return object.__setattr__(self, name, value)

        call, serial_val = get_setattr_call(self._name_, name, value)
        response = self._repl_.raw_run(call + ' = ' + serial_val)
        return object.__setattr__(self, name, create_jsobject(self._repl_, call, value))
    
    def __setitem__(self, name, value):
        """Set the given JSObject as an attribute of this JSObject and make proper javascript
        assignment on the other side of the bridge."""
        call, serial_val = get_setitem_call(self._name_, name, value)
        response = self._repl_.raw_run(call + ' = ' + serial_val)
        return object.__setitem__(self, name, create_jsobject(self._repl_, call, value))

    def _load(self, attributes_dict=None):
        """Load the full set of lazy loaded jsobjects for this object."""
        if attributes_dict is None:
            self._loaded_ = None
            inspection = self._repl_.run('Components.utils.import("resource://jsbridge/modules/inspection.js").inspect('+self._name_+')')
            inspect_dict, obj_type = parse_inspection(inspection)
            self_dict = create_jsobject_dict(self._repl_, self._name_, inspect_dict)
        else:
            self_dict = attributes_dict
        self.__dict__.update(self_dict)
        
        self._loaded_ = True
        
class JSFunction(JSObject):
    """Javascript function represenation.
    
    Returns a JSObject instance for the serialized js type with 
    name set to the full javascript call for this function. 
    """    
    def __call__(self, *args, **kwargs):
        assert len(kwargs) is 0
        fuuid, call = get_function_call(self._name_, args)
        name = 'Components.utils.import("resource://jsbridge/modules/controller.js").JSBridgeController.registry["' + fuuid + '"]'
        call = name + ' = ' + call
        self._repl_.run(call)
        value = self._repl_.run(self._repl_.back_channel.repl_name +'.print(' + name + ')')
        #Remove trailing endline
        value = value[:-1]
        return create_jsobject(self._repl_, name, value)

def init_jsobject(cls, repl, name, value):
    """Initialize a js object that is a subclassed base type; int, str, unicode, float."""
    obj = cls(value)
    obj._repl_ = repl
    obj._name_ = name
    return obj
        
class JSString(JSObject, unicode):
    "Javascript string representation."
    __init__ = unicode.__init__

class JSInt(JSObject, int): 
    """Javascript number representation for Python int."""
    __init__ = int.__init__

class JSFloat(JSObject, float):
    """Javascript number representation for Python float."""
    __init__ = float.__init__
    
class JSUndefined(JSObject):
    """Javascript undefined representation."""    
    __str__ = lambda self : "undefined"

    def __cmp__(self, other):
        if isinstance(other, JSUndefined):
            return True
        else:
            return False

    __nonzero__ = lambda self: False

js_type_cases = {'function'  :(JSFunction, False,), 
                  'object'   :(JSObject, False,), 
                  'array'    :(JSObject, False,),
                  'string'   :(JSString, True,), 
                  'number'   :(JSFloat, True,),
                  'undefined':(JSUndefined, False,),
                  }
py_type_cases = {unicode  :JSString,
                  str     :JSString,
                  int     :JSInt,
                  float   :JSFloat,
                  }
