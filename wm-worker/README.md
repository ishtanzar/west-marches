## West Marches Worker node
This is a simple worker node with a cron job that sends a notification in a discord channel every 5min for each entity that was modified on a kanka campaign

### How to use

You need a config file with your Kanka endpoint, discord channel id. Use the following as template:

```json
{
  "kanka": {
    "endpoint": "https://kanka.io/fr/campaign/xyz",
    "api_endpoint": "https://kanka.io/api/1.0/campaigns/xyz",
    "token": ""
  },
  "discord": {
    "kanka_notify_channel": 123456789,
    "token": ""
  },
  "cache": {
    "base_path": "/var/cache/wm-worker"
  }
}
```

Note: while kanka and discord tokens can be set using KANKA_TOKEN and DISCORD_BOT_SECRET environment variables, the config entries MUST exist, even as empty.

#### Docker (recommended)

```shell
docker run -d -v /path/to/config.json:/etc/wm-worker/config.json ishtanzar/wm-worker:latest
```

#### Python

While working, because of the defaults settings working with /etc and /var/cache, this may harm your system shall you be running as root.

```shell
python /path/to/project/wm-worker/src
```

### Architecture

This worker relies on asyncio to run an event loop which 3 jobs are running with:
- Quart http endpoint for the health endpoint at http://localhost:5000/health
- aiocron that owns the cron job every 5min and sends job to the asyncio.Queue
- a worker that processes any awaitable added to the asyncio.Queue