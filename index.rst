.. jsbridge documentation master file

jsbridge -- Python to Javascript bridge for Mozilla Applications
================================================================

.. toctree::
   :maxdepth: 3

.. _installation:

Installation
------------

`jsbridge` requires `setuptools <http://http://pypi.python.org/pypi/setuptools>`_. If you do not have them installed already you will want to.::

   $ curl -O http://peak.telecommunity.com/dist/ez_setup.py
   $ python ez_setup.py

If you are running Python 2.5 or earlier you will also need simplejson.::

   $ easy_install simplejson
   
On Windows you will also need pywin32 for mozrunner which can be downloaded `here <http://sourceforge.net/projects/pywin32/>`_.

`mozrunner` is another dependency you will need for jsbridge::

   $ easy_install mozrunner
   
Now you can install `jsbridge`.

The source code is publicly `available on github <http://github.com/mikeal/jsbridge>`_. 

The process for code contributions is for users to `fork the repository on github <http://help.github.com/forking/>`_, push modifications to their public fork, and then send `mikeal <http://github.com/mikeal>`_ a `pull request <http://github.com/guides/pull-requests>`_.

:mod:`jsbridge` --- Python to JavaScript bridge interface
=========================================================

.. module:: jsbridge
   :synopsis: Python to JavaScript bridge interface.
.. moduleauthor:: Mikeal Rogers <mikeal.rogers@gmail.com>
.. sectionauthor:: Mikeal Rogers <mikeal.rogers@gmail.com>


.. attribute:: extension_path

   Absolute path to the jsbridge XULRunner extension directory.
   
   This should be used by mozrunner when starting XULRunner applications::
   
      import mozrunner
      
      profile = mozrunner.FirefoxProfile(plugins=[jsbridge.extension_path])
      runner = mozrunner.FirefoxRunner(profile=profile, cmdargs=["-jsbridge", "24242"])
      runner.start()

.. function:: create_network(host, port)

   Returns a :class:`BackChannel` instance and a :class:`Bridge` instance 
   for the given host and port configuration::
   
      back_channel, bridge = create_network("127.0.0.1", 24242)

.. function:: wait_and_create_network(host, port[, timeout])
   
   Wait for the the given host/port to become available for connection
   or *timeout* and then run :func:`create_network`.
   
   *host* and *port* are the values to be passed to :func:`create_network`.
   
   Default *timeout* is `10`. *timeout* defines wait threshold in seconds.
      
.. class:: Bridge(host, port)

   Python to JavaScript TCP interface.
   
   *host* and *port* are :func:`str` and :func:`int` values respectively.

.. class:: BackChannel(host, port)

   Back channel callback TCP interface.
   
   *host* and *port* are string and integer values respectively.
   
   .. method:: add_listener(callback[, uuid[, eventType]])
   
   Add listener for events of a specified *uuid* or *eventType*.
   
   Any :func:`callable` can be used for *callback* argument. Should accept a single argument
   the result object.
   
   Callbacks can be specific to an individual event *uuid* or to all events of a given 
   *eventType*.
   
   .. method:: add_global_listener(callback)
   
   Add a listener to all events.
   
   Any :func:`callable` can be used as *callback*, should accept two positional arguments; 
   `eventType` and `result`.
   
.. class:: JSObject(bridge, name)

   Python representation of a live JavaScript object.
   
   Requires an instance of :class:`Bridge` and a :func:`str` of JavaScript to resolve the 
   object on the other side of the bridge.
   
   Once you have a :class:`JSObject` instance you can treat it like a normal Python object 
   and all attribute set/get operations and function calls will happen seamlessly 
   through the bridge:
    
      >>> runner.start()
      >>> back_channel, bridge = wait_and_create_network("127.0.0.1", 24242)
   
      >>> window_string = "Components.classes['@mozilla.org/appshell/window-mediator;1'].getService(Components.interfaces.nsIWindowMediator).getMostRecentWindow('')"
      >>> browser_window = JSObject(bridge, window_string)
      >>> browser_window.title
      u"Welcome to Firefox"
      >>> browser_window.title = "Remember; no matter where you go, there you are. - B. Banzai"
   
.. class:: CLI

   Command Line Interface.

   Inherits from :class:`mozrunner.CLI` and overrides relevant methods to start jsbridge.
   
   Also adds new command line options to for Python shell and debug modes.
   
Examples
--------

Starting jsbridge in your own script::
   
   import mozrunner
   import jsbridge
   
   profile = mozrunner.FirefoxProfile(plugins=[jsbridge.extension_path])
   runner = mozrunner.FirefoxRunner(profile=profile, cmdargs=["-jsbridge", "24242"])
   runner.start()
   
   back_channel, bridge = wait_and_create_network("127.0.0.1", 24242)
   
