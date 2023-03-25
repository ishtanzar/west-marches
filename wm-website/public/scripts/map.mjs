// noinspection JSUnresolvedVariable

import {hexMapConfig} from '/hexMap-config.mjs';
import {HexmapFactory} from '/scripts/hexmap.mjs';
import {WestMarches} from "./main.mjs";

/**
 * @type WestMarches
 */

// const KANKA_API_ENDPOINT = 'https://api.westmarches.localhost.lan:8443/kanka_api/1.0'
const KANKA_API_ENDPOINT = 'https://kanka.io/api/1.0'

let _map12, _backgroundOverlay;

export class WestMarchesMap extends WestMarches {

    async initialize() {
        await super.initialize();
        const baseDimensions = [3072, 4096];

        const Aberdeen = { lat: 1880.25, lng: 3665.125 }
        // const Aberdeen = { lat: baseDimensions[0], lng: 0 }
        const map = L.map('map', {
            crs: L.CRS.Simple,
            maxZoom: 2
        })
            .setView(Aberdeen, -5);

        const hexMap = new HexmapFactory(hexMapConfig.default);

        let moveTimeout = null;

        // ~12km map
        const map12 = _map12 = hexMap.build();
        map12.grid.pushAll(map12.hexGridFactory.rectangle({ height: map12.options.hexVert, width: map12.options.hexHoriz, onCreate: (hex => {
                hex.rendered = map12.svgGroup.use(map12.baseSymbol)
                    .translate(hex.toPoint().x + map12.options.offset.x, hex.toPoint().y + map12.options.offset.y)
            })}));

        // ~800m map
        const map800 = hexMap.build(hexMapConfig.map800);

        // ~ 35m map
        const map35 = hexMap.build(hexMapConfig.map35);

        // ~ 1.5m map
        const map5 = hexMap.build(hexMapConfig.map5);

        const crosshairIcon = L.icon({
            iconUrl: '/crosshair.png',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
        });

        const crosshair = L.marker(map.getCenter(), {icon: crosshairIcon, clickable:false});
        crosshair.addTo(map);

        _backgroundOverlay = L.imageOverlay('https://api.westmarches.localhost.lan:8443/map/0/charted.jpg', [[0,0], baseDimensions]).addTo(map);
        map12.overlay = L.svgOverlay(map12.svg.node, [[0,0], baseDimensions]).addTo(map);
        // L.svgOverlay(map800.svg.node, [[0,0], baseDimensions]).addTo(map);
        // L.svgOverlay(map35.svg.node, [[0,0], baseDimensions]).addTo(map);
        // L.svgOverlay(map5.svg.node, [[0,0], baseDimensions]).addTo(map);

        map12.center = map12.grid.get(map12.hexGridFactory.pointToHex(map12.fromLatLngToPoint(map.getCenter())));

        map35.svgGroup.use(map35.baseSymbol)

        map.on('mousemove', e => {
            const hexCoordinates = map12.hexGridFactory.pointToHex(map12.fromLatLngToPoint(e.latlng));
            const hex = map12.grid.get(hexCoordinates)
            if(hex) {
                if(map12.hexHover) { map12.hexHover.rendered.stroke({ color: map12.options.stroke.color }) }
                (map12.hexHover = hex).rendered.stroke({ color: '#f00' })
            }
        })

        map.on('move', () => {
            const center = map.getCenter();
            crosshair.setLatLng(center);

            map12.center = map12.grid.get(map12.hexGridFactory.pointToHex(map12.fromLatLngToPoint(map.getCenter())));
            map800.center = map800.grid.get(map800.hexGridFactory.pointToHex(map800.fromLatLngToPoint(map.getCenter())));
            map35.center = map35.grid.get(map35.hexGridFactory.pointToHex(map35.fromLatLngToPoint(map.getCenter())));
            map5.center = map5.grid.get(map5.hexGridFactory.pointToHex(map5.fromLatLngToPoint(map.getCenter())));

            clearTimeout(moveTimeout);

            moveTimeout = setTimeout(() => {
                history.pushState(null, null, `#${map12.center.x},${map12.center.y},0`);

                if(map.getZoom() >= 3) {
                    map800.hexGridFactory.hexagon({
                        radius: 13,
                        center: map800.hexFactory(map800.hexGridFactory.pointToHex(
                            map12.center.toPoint().x + map12.center.width() / 2 -  (2 * map800.options.hexSize / Math.sqrt(3)),
                            map12.center.toPoint().y + map12.center.height() / 2
                        )),
                        onCreate: hex => {
                            if(!map800.grid.get(hex)) {
                                hex.rendered = map800.svgGroup.use(map800.baseSymbol)
                                    .translate(hex.toPoint().x + map800.options.offset.x, hex.toPoint().y + map800.options.offset.y)
                                map800.grid.push(hex);
                            }
                        }
                    });
                }

                if(map.getZoom() >= 7) {
                    map35.hexGridFactory.hexagon({
                        radius: 16,
                        center: map35.hexFactory(map35.hexGridFactory.pointToHex(
                            map800.center.toPoint().x + map800.center.width() / 2,
                            map800.center.toPoint().y + map800.center.height() / 2
                        )),
                        onCreate: hex => {
                            if(!map35.grid.get(hex)) {
                                hex.rendered = map35.svgGroup.use(map35.baseSymbol)
                                    .translate(hex.toPoint().x + map35.options.offset.x, hex.toPoint().y + map35.options.offset.y)
                                map35.grid.push(hex);
                            }
                        }
                    });
                }

                if(map.getZoom() >= 11) {
                    map5.hexGridFactory.hexagon({
                        radius: 13,
                        center: map5.hexFactory(map5.hexGridFactory.pointToHex(
                            map35.center.toPoint().x + map35.center.width() / 2,
                            map35.center.toPoint().y + map35.center.height() / 2
                        )),
                        onCreate: hex => {
                            if(!map5.grid.get(hex)) {
                                hex.rendered = map5.svgGroup.use(map5.baseSymbol)
                                    .translate(hex.toPoint().x + map5.options.offset.x, hex.toPoint().y + map5.options.offset.y)
                                map5.grid.push(hex);
                            }
                        }
                    });
                }
            }, 50)
        });

        map.on('zoom', () => {
            const zoom = map.getZoom();

            if(zoom <= 3) map12.svg.show(); else map12.svg.hide();
            if(_.inRange(zoom, 3, 8)) map800.svg.show(); else map800.svg.hide();
            if(_.inRange(zoom, 7, 15)) map35.svg.show(); else map35.svg.hide();

            map12.svgGroup.stroke({ width: map12.options.stroke.width / Math.pow(2, map.getZoom()) });
            if(zoom >= 7) {
                map800.svgGroup.stroke({ width: map800.options.stroke.width / Math.pow(2, map.getZoom() - 4) });
            }
            if(zoom >= 11) {
                map35.svgGroup.stroke({ width: map35.options.stroke.width / Math.pow(2, map.getZoom() - 8) });
            }
        });

        // map.addControl(new L.Control.GM_Tools(this, { position: 'topleft' }));
        // map.addControl(new L.Control.Player_Tools(this, { position: 'topleft' }));

        _backgroundOverlay.on('load', () => {
            const flyto = window.location.hash?.substring(1);
            if(flyto && flyto.match(/\d{0,3},\d{0,3},\d/)) {
                const [x,y,z] = flyto.split(',');
                map.flyTo(map12.fromHexToLatLng(map12.hexFactory(parseInt(x), parseInt(y))))
            }
        })
    }

    get map12() {
        return _map12;
    }

    get backgroundOverlay() {
        return _backgroundOverlay;
    }
}
