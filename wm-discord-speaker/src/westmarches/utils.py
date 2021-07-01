import json
import logging
from abc import ABC

from discord.ext.commands import Context
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import commands

log = logging.getLogger("red.westmarches")


def log_message(ctx: Context):
    log.info(json.dumps({
        "user": '%s#%s' % (ctx.author.name, ctx.author.id),
        "command": ctx.command.qualified_name,
        "data": {
            "guild": '{}#{}'.format(ctx.guild.name, ctx.guild.id),
            "channel": '{}#{}'.format(ctx.channel.name, ctx.channel.id),
            "_raw": str(ctx.message)
        },
    }))


class DiscordProgress:

    def __init__(self, ctx, config: Config, key_prefix) -> None:
        self.ctx = ctx
        self.config = config
        self.key_prefix = key_prefix

    async def __aenter__(self):
        log_message(self.ctx)

        async with self.config.messages() as messages:
            await self.ctx.send(messages[self.key_prefix + '.started'])

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self.config.messages() as messages:
            await self.ctx.send(messages[self.key_prefix + '.done'])


class MixinMeta(ABC):
    bot: Red
    config: Config


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass
