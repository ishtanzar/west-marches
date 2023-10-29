import logging

import discord
from discord.ext.commands import Context
from elasticsearch import AsyncElasticsearch as Elasticsearch
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import commands
from socketio import AsyncClient
from westmarches_utils.api import WestMarchesApi
from westmarches_utils.api.exception import HTTPException

log = logging.getLogger("red.westmarches.abstract")

class AbstractCommand(commands.Cog):
    bot: Red
    config: Config
    io: AsyncClient
    wm_api: WestMarchesApi
    es: Elasticsearch

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._on_message_without_command_handlers = []

    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        async with self.config.messages() as _messages:
            messages = _messages

        try:
            await ctx.send(messages[messages_key + '.started'])
            await f()
            await ctx.send(messages[messages_key + '.done'])
        except HTTPException:
            await ctx.send(messages[messages_key + '.failed'])

    async def _get_thread_original_message(self, channel: discord.Thread):
        try:
            async for starter_message in channel.history(limit=1, oldest_first=True):
                if starter_message.type is discord.MessageType.thread_starter_message:
                    return starter_message.reference.resolved
        except Exception as e:
            log.warning(str(e), exc_info=True)

    async def _get_thread_original_message_mentions(self, channel: discord.Thread, guild: discord.Guild):
        members = []
        original_message = await self._get_thread_original_message(channel)

        for user in original_message.mentions:
            members.append((await guild.query_members(user_ids=[user.id]))[0])

        return members


from .forward import Forward
from .foundryvtt import FoundryCommands
from .inkarnate import InkarnateCommands
from .kanka import KankaCommands
from .management import ManagementCommands
from .sessions import SessionsCommands
