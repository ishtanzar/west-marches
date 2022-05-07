
export default class Actors {
  async get(req, res) {
    try {
      res.set('Content-Type', 'application/json');

      const players = await db['User'].db.findMany({'role': { $lt: 4 }});
      const users_ids = players.map(function(user) { return user._id });

      const actors = await db['Actor'].db.findMany({ $where: function () {
          const owners = Object.entries(this.permission)
            .map(function([user, level]) { return level === 3 ? user : null })
            .filter(function(user) {
              return users_ids.indexOf(user) !== -1;
            });
          return owners.length > 0;
        }});

      res.send({'actors': actors});
    } catch (ex) {
      res.status(500).end(ex.toString());
    }
  }
}
