
const baseHexSize = 26.96;

const map800HexSize = (2 * baseHexSize) / (15 * Math.sqrt(3));
const map35HexSize = (2 * map800HexSize) / (25 * Math.sqrt(3));
const map5HexSize = (2 * map35HexSize) / (23 * Math.sqrt(3));

const defaultOffset = {x: -3, y: 0}
const map800Offset = {
    x: defaultOffset.x,
    y: defaultOffset.y - map800HexSize / 4
}
const map35Offset = {
    x: map800Offset.x - map35HexSize / 4,
    y: map800Offset.y
}
const map5Offset = {
    x: map35Offset.x,
    y: map35Offset.y - map5HexSize / 4
}

export const hexMapConfig = {
    default: {
        width: 4096,
        height: 3072,
        hexVert: 66,
        hexHoriz: 122,
        hexSize: baseHexSize,
        offset: defaultOffset,
        orientation: 'flat',
        stroke: { width: 1, color: '#ccc' },
    },
    map800: {
        hexSize: map800HexSize,
        offset: map800Offset,
        orientation: 'pointy',
        stroke: { width: 0.2 }
    },
    map35: {
        hexSize: map35HexSize,
        offset: map35Offset,
        stroke: { width: 0.01 }
    },
    map5: {
        hexSize: map5HexSize,
        offset: map5Offset,
        orientation: 'pointy',
        stroke: { width: 0.0005 }
    }
};