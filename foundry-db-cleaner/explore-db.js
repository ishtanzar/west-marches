var Datastore = require('nedb'), dbName = "actors", db = new Datastore({
  filename: './data/worlds/west-marches-de-la-cave/data/' + dbName + '.db',
  autoload: true
});

db.findOne({_id: 'aIKXLw64AG0brGMs'}, function (err, doc) {
  var count = 0
  for(item of doc["items"]) {
    if(item["type"] == "spell" && item["name"] == "New Spell") {
      count++
      // break;
    }
  }
  console.log(count)
})

// var types = {}
// db.find({}, function (err, docs) {
//   for(let doc of docs) {
//     let type = doc.type;
//
//     if(type in types) {
//       types[type] += 1;
//     } else {
//       types[type] = 1;
//     }
//   }
//   console.log(types);
// });



