import logging.config
import os

import socketio
from discord.ext.commands import Context
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from . import commands
from .api import WestMarchesApiClient, BasicAuth, HTTPException
from .utils import CompositeMetaClass, log_message

log = logging.getLogger('red.westmarches')


class WestMarchesCog(commands.Commands,
                     Cog,
                     metaclass=CompositeMetaClass):

    def __init__(self, bot: Red, io: socketio.AsyncClient, config: dict):
        super().__init__()

        self.bot = bot
        self.io = io
        self.setup_events()

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**config)

        api_auth = BasicAuth('foundry_manager', os.environ['WM_API_SECRET'])
        self.api_client = WestMarchesApiClient(api_auth, os.environ['WM_API_ENDPOINT'])

        log.info("WestMarches loaded")

    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        async with self.config.messages() as _messages:
            messages = _messages

        try:
            await ctx.send(messages[messages_key + '.started'])
            await f()
            await ctx.send(messages[messages_key + '.done'])
        except HTTPException:
            await ctx.send(messages[messages_key + '.failed'])

    def setup_events(self):
        @self.bot.event
        async def on_command(ctx: Context):
            log_message(ctx)
