import json
import logging
import logging_utilities.formatters.json_formatter
import os
import socketio
from logging.handlers import RotatingFileHandler
from redbot.core.bot import Red
from types import SimpleNamespace

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

    await bot.add_cog(WestMarchesCog(
        bot=bot,
        io=io,
        config=config_dict
    ))
