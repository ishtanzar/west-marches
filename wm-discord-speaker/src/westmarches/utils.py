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
        "user": '{}#{}'.format(ctx.author.name, ctx.author.id),
        "command": ctx.command.qualified_name,
        "data": {
            "guild": '{}#{}'.format(ctx.guild.name, ctx.guild.id),
            "channel": '{}#{}'.format(ctx.channel.name, ctx.channel.id),
            "_raw": str(ctx.message)
        },
    }))


class MixinMeta(ABC):
    bot: Red
    config: Config


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass
