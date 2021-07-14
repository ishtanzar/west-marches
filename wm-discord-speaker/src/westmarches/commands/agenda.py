from abc import abstractmethod
from urllib.parse import urlparse, ParseResult

import validators
from discord import User
from discord.ext.commands import Context
from redbot.core import commands

from westmarches.utils import MixinMeta, CompositeMetaClass


class AgendaCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        pass

    @commands.command(rest_is_raw=True)
    async def schedule(self, ctx: commands.Context, *, arg: str):
        (date_str, announce) = arg.strip().split('\n', maxsplit=1)
        session_gm: User = ctx.message.author

        if validators.url(announce):
            url: ParseResult = urlparse(announce)
            (_, server_id, channel_id, message_id) = url.path[1:].split('/')

            session_dict = await self.api_client.sessions.schedule(date_str, {
                'channel_id': channel_id,
                'message_id': message_id,
            })

            async with self.config.messages() as messages:
                await ctx.send(messages['sessions.schedule.done'].format(
                    'https://kanka.io/en/campaign/67312/journals/' + str(session_dict['journal'])
                ))
