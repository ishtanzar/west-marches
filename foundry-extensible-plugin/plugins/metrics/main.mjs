import prom from "prom-client";

export default class MetricsPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    this.gauges = [];
    this.metrics = [
      {db: 'Actor', name: 'actors'},
      {db: 'Item', name: 'items'},
      {db: 'Scene', name: 'scenes'},
      {db: 'Note', name: 'notes'},
      {db: 'JournalEntry', name: 'journals'},
      {db: 'ChatMessage', name: 'chat_messages'},
      {db: 'Macro', name: 'macros'},
      {db: 'User', name: 'users'},
    ];

    for(let metric of this.metrics) {
      this[metric.name] = 0;
    }

    base.hooks.on('pre.express.defineRoutes', router => router.get('/metrics', this.get));
    this.setup().update().schedule();
  }

  setup() {
    const self = this;

    prom.collectDefaultMetrics();

    this.gauges.push(new prom.Gauge({
      name: 'foundry_users_active_total',
      help: 'Currently active users',
      collect() {
        const {game} = global;

        if(game && game.activity && game.activity.users) {
          this.set(Object.values(game.activity.users).length)
        }
      }
    }));

    this.gauges.push(new prom.Gauge({
      name: 'foundry_uptime',
      help: 'Server Uptime',
      collect() {
        const {game} = global;

        if(game && game.activity) {
          this.set(game.activity.serverTime)
        }
      }
    }));

    this.gauges.push(new prom.Gauge({
      name: 'foundry_db_entities_total',
      help: 'Size of DB table for each entity type',
      labelNames: ['db'],
      collect() {
        for(let metric of self.metrics) {
          this.set({ db: metric.db }, self[metric.name])
        }
      }
    }));

    return this;
  }

  update() {
    const {db, game} = global;

    if(game && game.active) {
      for(let metric of this.metrics) {
        if(db[metric.db] && db[metric.db].connected) {
          db[metric.db].db.count({}, function (err, count) {
            this[metric.name] = count;
          }.bind(this));
        }
      }
    }

    return this;
  }

  schedule() {
    setTimeout(function () {
      try {
        this.update();
      } catch (ex) {}

      this.schedule();
    }.bind(this), 600);

    return this;
  }

  async get(req, res) {
    try {
      res.set('Content-Type', prom.register.contentType)
      res.send(await prom.register.metrics());
    } catch (ex) {
      res.status(500).end(ex.toString());
    }
  }
}
