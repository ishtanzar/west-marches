// noinspection JSUnresolvedVariable

L.WestMarches = {};

let _activeHandler, _defaultHandler;

L.WestMarches.Utils = {
    activate: function (handler) {
        if(_activeHandler) _activeHandler.disable();
        _activeHandler = handler;
    },
    setDefaultHandler: function (handler) {
        _defaultHandler = handler;
    },
    getDefaultHandler: function () {
        return _defaultHandler;
    },
    createButton: function (options) {
        const link = L.DomUtil.create('a', options.className || '', options.container);

        link.href = '#';

        if (options.title) {
            link.title = options.title;
        }

        if (options.text) {
            link.innerHTML = options.text;
        }

        L.DomEvent
            .on(link, 'click', L.DomEvent.stopPropagation)
            .on(link, 'mousedown', L.DomEvent.stopPropagation)
            .on(link, 'dblclick', L.DomEvent.stopPropagation)
            .on(link, 'touchstart', L.DomEvent.stopPropagation)
            .on(link, 'click', L.DomEvent.preventDefault)
            .on(link, 'click', options.callback, options.context);

        return link;
    },
}