import logging

from discord.ext.commands import Context
from redbot.core import Config

log = logging.getLogger("red.westmarches")


def log_message(ctx: Context):
    data = {
        'discord': {
            'message': {
                'id': ctx.message.id,
                'channel': ctx.message.channel,
                'content': ctx.message.content,
                'author': ctx.message.author,
                'guild': ctx.message.guild,
            },
            'prefix': ctx.prefix,
            'command': ctx.command,
            'command_failed': ctx.command_failed,
        }
    }
    log.info('%s#%d: %s', ctx.author.name, ctx.author.id, ctx.message.content, extra=data)


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
