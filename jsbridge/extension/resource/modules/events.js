var EXPORTED_SYMBOLS = ["fireEvent"]

var server = {}; Components.utils.import('resource://jsbridge/modules/server.js', server);

var fireEvent = server.Events.fireEvent;

