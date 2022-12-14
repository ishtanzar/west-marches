import collections
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from types import SimpleNamespace

import logging_utilities.formatters.json_formatter
import socketio
from redbot.core.bot import Red

from .cog import WestMarchesCog
from .websocket import MapNamespace

log = logging.getLogger('red.westmarches')


async def setup(bot: Red):
    config = {}

    def hook(data):
        if data.get("__tuple__", None):
            del data["__tuple__"]
            return dict(data.items())
        return SimpleNamespace(**data)

    with open(os.environ['CONFIG_PATH']) as fp:
        config = json.load(fp, object_hook=hook)

    handler = RotatingFileHandler(
        config.log.handlers.json.filename,
        maxBytes=1048576,
        backupCount=1
    )

    handler.setFormatter(logging_utilities.formatters.json_formatter.JsonFormatter(
        fmt=config.log.handlers.json.fmt,
        add_always_extra=True
    ))
    logging.getLogger().addHandler(handler)

    config_dict = json.loads(json.dumps(config, default=lambda x: vars(x)))
    io = socketio.AsyncClient()
    io.register_namespace(MapNamespace())

    # log.info("Connecting to API websocket")
    # await io.connect('ws://api:3000/')

    bot.add_cog(WestMarchesCog(bot, io, config_dict))
