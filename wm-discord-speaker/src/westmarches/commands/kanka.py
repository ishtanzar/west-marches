import discord
import os
import requests

from abc import abstractmethod
from discord.ext.commands import Context
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta


class KankaCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        pass

    def __init__(self, endpoint='https://kanka.io/api/1.0/campaigns/67312'):
        self._token = os.environ['KANKA_TOKEN']
        self._endpoint = endpoint

    @checks.has_permissions(administrator=True)
    @commands.group(name="kanka")
    async def command_kanka(self, ctx: commands.Context):
        """Kanka admin commands"""

    @command_kanka.command()
    async def list_users(self, ctx: commands.Context, user_filter: str = ''):
        users = requests.get(self._endpoint + '/users', headers={'Authorization': 'Bearer ' + self._token}).json()
        resp = "\n".join([u['name'] for u in users['data'] if user_filter.lower() in u['name'].lower()])
        async with self.config.messages() as messages:
            await ctx.send(resp if resp else messages['kanka.users.list.not_found'])

    # @command_kanka.command()
    # async def user_set_gm(self, ctx: commands.Context, user_str: str):

    @command_kanka.command(name="reports_channel")
    async def set_reports_channel(self, ctx: commands.Context):
        await self.config.kanka_reports_channel.set(ctx.channel.id)
        await ctx.message.add_reaction('\U00002705')  # :white_check_mark:

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx = await self.bot.get_context(message)  # type: commands.Context

        if ctx.channel.id == await self.config.kanka_reports_channel():
            await ctx.message.add_reaction('\U0001F5FA')  # :white_check_mark:
