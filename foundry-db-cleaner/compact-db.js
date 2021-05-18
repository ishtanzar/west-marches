var Datastore = require('nedb');

for (const dbName of ["actors", "chat", "fog", "journal"]) {
  db = new Datastore({
    filename: './data/worlds/west-marches-de-la-cave/data/' + dbName + '.db',
    autoload: true
  });
  db.persistence.compactDatafile();
}


