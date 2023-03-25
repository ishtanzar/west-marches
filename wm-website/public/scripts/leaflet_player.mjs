// noinspection JSUnresolvedVariable

const KANKA_API_ENDPOINT = 'https://kanka.io/api/1.0'

let _offcanvasMap, _bsOffcanvas;

L.WestMarches.Explore = L.Handler.extend({
    /**
     *
     * @param westMarchesMap {WestMarchesMap}
     * @param map
     * @param options
     */
    initialize: function (westMarchesMap, map, options) {
        L.Handler.prototype.initialize.call(this, map, options);
        this._westMarchesMap = westMarchesMap;
    },
    addHooks: function () {
        L.WestMarches.Utils.activate(this);

        if (this._map) {
            this._map.on('click', this._onClick, this);
        }
    },
    removeHooks: function () {
        if (this._map) {
            this._map.off('click', this._onClick, this);
        }
    },
    _onClick: async function (e) {
        const zoom = this._map.getZoom();

        if(zoom <= 3) {
            const hexmap = this._westMarchesMap.map12;
            const hex = hexmap.grid.get(hexmap.fromLatLngToHex(e.latlng))
            if(hex) {
                const api_url = new URL(`${KANKA_API_ENDPOINT}/campaigns/93396/journals`);

                api_url.searchParams.append('attribute_name', '_hex_coordinates');
                api_url.searchParams.append('attribute_value', `{"x": ${hex.x}, "y": ${hex.y}, "z": 0}`);

                const resp = await fetch(api_url.href, {
                    mode: 'cors',
                    headers: {
                        'Authorization': 'Bearer ' + this._westMarchesMap.kankaToken,
                        'Content-type': 'application/json'
                    }
                });
                await this._listReports(hex, (await resp.json()).data)
            }
        }
    },

    _listReports: async function (hex, reportList) {
        const resp = await fetch('/templates/reports.jst');
        const compiled = _.template(await resp.text());

        $('.offcanvas-title', _offcanvasMap).html(`Hex ${hex.x},${hex.y},0`)
        $('.offcanvas-body', _offcanvasMap).html(compiled({'reports': reportList}));
        _bsOffcanvas.show();
    }
})

L.WestMarches.Report = L.Handler.extend({
    options: {
        icon: new L.Icon.Default(),
        repeatMode: false,
        zIndexOffset: 2000 // This should be > than the highest z-index any markers
    },
    addHooks: function () {
        if (this._map) {
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
                .on('click', this._onClick, this)
                .addTo(this._map);

            this._map.on('mousemove', this._onMouseMove, this);
            this._map.on('click', this._onTouch, this);
        }
    },
    removeHooks: function () {
        if (this._map) {
            this._map
                .off('click', this._onClick, this)
                .off('click', this._onTouch, this);
            if (this._marker) {
                this._marker.off('click', this._onClick, this);
                this._map.removeLayer(this._marker);
                delete this._marker;
            }

            this._mouseMarker.off('click', this._onClick, this);
            this._map.removeLayer(this._mouseMarker);
            delete this._mouseMarker;

            this._map.off('mousemove', this._onMouseMove, this);
        }
    },

    _onMouseMove: function (e) {
        let latlng = e.latlng;

        this._mouseMarker.setLatLng(latlng);

        if (!this._marker) {
            this._marker = this._createMarker(latlng);
            // Bind to both marker and map to make sure we get the click event.
            this._marker.on('click', this._onClick, this);
            this._map
                .on('click', this._onClick, this)
                .addLayer(this._marker);
        }
        else {
            latlng = this._mouseMarker.getLatLng();
            this._marker.setLatLng(latlng);
        }
    },

    _createMarker: function (latlng) {
        return new L.Marker(latlng, {
            icon: this.options.icon,
            zIndexOffset: this.options.zIndexOffset
        });
    },

    _onClick: function () {
        const marker = new L.Marker(this._marker.getLatLng(), {icon: this.options.icon});
        console.log(marker)
        this.disable();
    },

    _onTouch: function (e) {
        // called on click & tap, only really does any thing on tap
        this._onMouseMove(e); // creates & places marker
        this._onClick(); // permanently places marker & ends interaction
    },

})

L.Control.Player_Tools = L.Control.extend({
    /**
     *
     * @param westMarchesMap {WestMarchesMap}
     * @param options
     */
    initialize: function (westMarchesMap, options) {
        L.Control.prototype.initialize.call(this, options);

        this._westMarchesMap = westMarchesMap;

        _offcanvasMap = $('#offcanvasMap');
        _bsOffcanvas = new bootstrap.Offcanvas(_offcanvasMap);

    },
    onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-player')
        L.DomUtil.create('a', '', container).innerHTML = 'PJ'

        const explore = this._addExploringTool()
        this._addReportingTool(map, container)

        L.WestMarches.Utils.setDefaultHandler(explore);
        explore.enable();

        return container
    },
    onRemove: function(map) {},
    _addExploringTool: function () {
        return new L.WestMarches.Explore(this._westMarchesMap, this._map);
    },
    _addReportingTool: function(map, container) {
        const handler = new L.WestMarches.Report(map, {})
        const link = L.WestMarches.Utils.createButton({
            container: container,
            text: '📍',
            callback: handler.enable,
            context: handler
        });
    }
})
