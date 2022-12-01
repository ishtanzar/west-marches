export class Hexmap {
    options;

    hexFactory;
    svg;
    svgGroup;
    hexGridFactory;
    baseSymbol;
    center;
    grid;

    constructor(options) {
        this.options = options;

        this.hexFactory = Honeycomb.extendHex({
            size: options.hexSize,
            orientation: options.orientation
        });

        this.svg = SVG()
            .size(options.width, options.height)
            .viewbox(0, 0, options.width, options.height);

        this.svgGroup = this.svg.group()
            .fill('none')
            .stroke(options.stroke);

        this.hexGridFactory = Honeycomb.defineGrid(this.hexFactory);
        this.grid = this.hexGridFactory()
        this.baseSymbol = this.svg.symbol().polygon(this.hexFactory().corners().map(({ x, y }) => `${x},${y}`));

    }

    fromLatLngToPoint(latlng) {
        return Honeycomb.Point({
            x: latlng.lng - this.options.offset.x,
            y: (3072 - latlng.lat) - this.options.offset.y
        })
    }

    fromLatLngToHex(latlng) {
        return this.hexGridFactory.pointToHex(this.fromLatLngToPoint(latlng));
    }

    fromHexToLatLng(hex) {
        const point = hex.toPoint()
        return {
            lng: point.x + this.options.offset.x + (this.hexFactory().width() / 2),
            lat: 3072 - point.y - this.options.offset.y - (this.hexFactory().height() / 2)
        }
    }
}

export class HexmapFactory {
    defaultMapOptions;

    constructor(defaultMapOptions) {
        this.defaultMapOptions = defaultMapOptions;
    }

    build(opts) {
        const options = _.merge({}, this.defaultMapOptions, opts);
        return new Hexmap(options);
    }
}
