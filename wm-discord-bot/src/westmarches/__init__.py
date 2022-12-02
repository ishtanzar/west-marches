import socketio
from redbot.core.bot import Red

from .cog import WestMarchesCog
from .websocket import MapNamespace


async def setup(bot: Red):
    io = socketio.AsyncClient()
    io.register_namespace(MapNamespace())

    await io.connect('ws://api:3000/')
    bot.add_cog(WestMarchesCog(bot, io))
