'use strict';

const {paths} = global;

const Document = require(paths.code + '/database/odm/document');

class ExtensibleDocument extends Document {

}

exports.default = ExtensibleDocument;
module.exports = ExtensibleDocument;
