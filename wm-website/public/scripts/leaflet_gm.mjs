/**
 * @class L.WestMarches.Chart
 * @inherits L.Handler
 */
L.WestMarches.Chart = L.Handler.extend({
    initialize: function (hexmap, map, options) {
        L.Handler.prototype.initialize.call(this, map, options);

        L.WestMarches.Chart.include(L.Mixin.Events);

        this._hexMap = hexmap;
    },
    enable: function () {
        L.Handler.prototype.enable.call(this);
        this.fire('enabled');
    },
    disable: function () {
        L.Handler.prototype.disable.call(this);
        this.fire('disabled');
    },
    reset: function () {
        for (const hex of this._inprogressHexMap) {
            this._hexMap.grid.get(hex).rendered.attr('fill', null)
        }
        this._inprogressHexMap = this._hexMap.hexGridFactory()
    },
    addHooks: function () {
        L.WestMarches.Utils.activate(this);

        if (this._map) {
            this._mapDraggable = this._map.dragging.enabled();
            this._inprogressHexMap = this._hexMap.hexGridFactory()

            if (this._mapDraggable) {
                this._map.dragging.disable();
            }

            if (!this._mouseMarker) {
                this._mouseMarker = L.marker(this._map.getCenter(), {
                    icon: L.divIcon({
                        className: 'leaflet-mouse-marker',
                        iconAnchor: [20, 20],
                        iconSize: [40, 40]
                    }),
                    opacity: 0,
                    zIndexOffset: this.options.zIndexOffset
                });
            }

            this._mouseMarker
                .on('mousemove', this._onMouseMove, this) // Necessary to prevent 0.8 stutter
                .on('mousedown', this._onMouseDown, this)
                .addTo(this._map);

            this._map
                .on('mousemove', this._onMouseMove, this)
                .on('touchstart', this._onMouseDown, this)
                .on('touchmove', this._onMouseMove, this);

            document.addEventListener('touchstart', L.DomEvent.preventDefault, {passive: false});
        }
    },
    removeHooks: function () {
        if (this._map) {
            this.reset();

            if (this._mapDraggable) {
                this._map.dragging.enable();
            }

            this._mouseMarker
                .off('mousedown', this._onMouseDown, this)
                .off('mousemove', this._onMouseMove, this);
            this._map.removeLayer(this._mouseMarker);
            delete this._mouseMarker;

            this._map
                .off('mousemove', this._onMouseMove, this)
                .off('touchstart', this._onMouseDown, this)
                .off('touchmove', this._onMouseMove, this);
        }

        L.DomEvent.off(document, 'mouseup', this._onMouseUp, this);

        document.removeEventListener('touchstart', L.DomEvent.preventDefault);
        L.WestMarches.Utils.getDefaultHandler()?.enable();
    },
    getHexMap: function() {
        return this._inprogressHexMap;
    },
    _onMouseMove: function (e) {
        this._mouseMarker.setLatLng(e.latlng);

        if (this._isDrawing) {
            const hex = this._hexMap.hexGridFactory.pointToHex(this._hexMap.fromLatLngToPoint(e.latlng));
            if(hex !== this._lastHex) {
                this._lastHex = hex;
                if(!this._inprogressHexMap.includes(hex)) {
                    this._hexMap.grid.get(hex).rendered
                        .fill({ color: '#ff0', opacity: 0.8 })
                    // .stroke({ color: '#fa0'})
                    this._inprogressHexMap.push(hex);
                }
            }
        }
    },
    _onMouseDown: function (e) {
        this._isDrawing = true;
        this._onMouseMove(e)

        L.DomEvent.on(document, 'mouseup', this._onMouseUp, this)
    },
    _onMouseUp: function () {
        this._isDrawing = false;
    }
})

L.Control.GM_Tools = L.Control.extend({
    /**
     *
     * @param westMarchesMap {WestMarchesMap}
     * @param options
     */
    initialize: function (westMarchesMap, options) {
        L.Control.prototype.initialize.call(this, options);
        this._westMarchesMap = westMarchesMap;
    },
    onAdd: function() {
        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-gm')
        L.DomUtil.create('a', '', container).innerHTML = 'MJ'

        this._addCartographerTool(this._westMarchesMap.map12, this._map, container)

        return container
    },
    onRemove: function() {},
    _addCartographerTool: function (hexmap, map, container) {
        const handler = new L.WestMarches.Chart(hexmap, map, {})
        const link = L.WestMarches.Utils.createButton({
            container: container,
            text: '🗺️',
            callback: handler.enable,
            context: handler
        });

        const actionsContainer = L.DomUtil.create('ul', 'leaflet-wm-actions', link);

        const saveAction = L.WestMarches.Utils.createButton({
            container: L.DomUtil.create('li', '', actionsContainer),
            text: 'Save',
            callback: () => {
                fetch('https://api.westmarches.localhost.lan:8443/map/0/charted.json', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        hexmap: handler.getHexMap().map(hex => ({"x": hex.x, "y":hex.y, "charted": true }))
                    })
                }).then(() => {
                    const imgUrl = new URL(this._westMarchesMap.backgroundOverlay._url);
                    imgUrl.searchParams.set('t', Date.now().toString());
                    this._westMarchesMap.backgroundOverlay.setUrl(imgUrl);

                    handler.reset();
                });
            },
            context: this
        });

        const cancelAction = L.WestMarches.Utils.createButton({
            container: L.DomUtil.create('li', '', actionsContainer),
            text: 'Cancel',
            callback: handler.disable,
            context: handler
        });

        handler.on('enabled', () => {
            actionsContainer.style.top = `${link.offsetTop}px`;
            actionsContainer.style.left = `${link.offsetWidth}px`;
            actionsContainer.style.display = 'block';
            link.style.borderBottomRightRadius = '0';
        }, this)

        handler.on('disabled', () => {
            actionsContainer.style.display = '';
            link.style.borderBottomRightRadius = '';
        }, this)

    }
});
