
export default class Activity {

  async get(req, res) {
    try {
      res.set('Content-Type', 'application/json');
      res.send({
        'users': (await Promise.all(Object.keys(game.activity.users).map(u => db.User.get(u)))).map(u => u.name)
      });
    } catch (ex) {
      res.status(500).end(ex.toString());
    }
  }

}