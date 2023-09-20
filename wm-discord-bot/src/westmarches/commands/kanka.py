from http.client import HTTPException

from typing import Optional

import os
from abc import abstractmethod

import discord
import requests
from discord import Member
from discord.ext.commands import Context
from discord.raw_models import RawReactionActionEvent
from redbot.core import commands, checks

from westmarches_utils.api import DiscordUser
from westmarches.utils import CompositeMetaClass, MixinMeta


class CustomReactionActionEvent:

    def __init__(self, message_id, channel_id, user_id, guild_id, emoji) -> None:
        self.message_id = message_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.emoji = emoji

    @staticmethod
    def from_raw(raw: RawReactionActionEvent):
        return CustomReactionActionEvent(raw.message_id, raw.channel_id, raw.user_id, raw.guild_id, raw.emoji.name)


class KankaCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._token = os.environ['KANKA_TOKEN']
        # self._es = es

    @checks.has_permissions(administrator=True)
    @commands.group(name="kanka")
    async def command_kanka(self, ctx: commands.Context):
        """Kanka admin commands"""

    @command_kanka.command()
    async def list_users(self, ctx: commands.Context, user_filter: str = ''):
        users = requests.get(
            await self.config.kanka.endpoint() + '/users',
            headers={'Authorization': 'Bearer ' + self._token}
        ).json()

        resp = "\n".join([u['name'] for u in users['data'] if user_filter.lower() in u['name'].lower()])
        async with self.config.messages() as messages:
            await ctx.send(resp if resp else messages['kanka.users.list.not_found'])

    async def update_kanka_roles(self, ctx: commands.Context, discord_user: Member, add: Optional[int] = None, remove: Optional[int] = None):
        try:
            api_user = (await self.wm_api.users.findOne({'discord.id': str(discord_user.id)}))['value']

            if api_user and (kanka_user_id := api_user.get('kanka', {}).get('id')):
                if add:
                    requests.post(
                        await self.config.kanka.endpoint() + '/users',
                        headers={'Authorization': 'Bearer ' + self._token},
                        json={
                            'user_id': kanka_user_id,
                            'role_id': add
                        }
                    )
                if remove:
                    requests.delete(
                        await self.config.kanka.endpoint() + '/users',
                        headers={'Authorization': 'Bearer ' + self._token},
                        json={
                            'user_id': kanka_user_id,
                            'role_id': remove
                        }
                    )
                await ctx.message.add_reaction('\U00002705')
            else:
                async with self.config.messagees() as messages:
                    await ctx.send(messages['kanka.users.find.not_found'] % discord_user.name)

        except HTTPException as e:
            await ctx.send(str(e))

    @command_kanka.command(name="set_gm")
    async def set_kanka_gm(self, ctx: commands.Context, member: Optional[Member]):
        if not member:
            member = ctx.author

        await self.update_kanka_roles(
            ctx,
            member,
            add=await self.config.kanka.gm_role(),
            remove=await self.config.kanka.player_role()
        )

    @command_kanka.command(name="remove_gm")
    async def remove_kanka_gm(self, ctx: commands.Context, member: Optional[Member]):
        if not member:
            member = ctx.author

        await self.update_kanka_roles(
            ctx,
            member,
            add=await self.config.kanka.player_role(),
            remove=await self.config.kanka.gm_role()
        )

    @command_kanka.command()
    async def search(self, ctx: commands.Context, query: str):
        resp = await self.es.search(index='kanka_*', query={
            'query_string': {
                'query': query,
                'fields': ["name^5", "*.name^3", "child.entry"]
            }
        }, highlight={
            'fields': {
                '*.*': {}
            }
        }, size=50)

        hits = {}
        for doc in resp['hits']['hits']:
            source = doc.get('_source', {})
            type_ = source.get('type')

            if type_ in hits and len(hits[type_]) <= 3:
                hits[type_].append(source)
            else:
                hits[type_] = [source]

        msg = ''
        for type_ in hits:
            msg += type_ + ' :\n'
            for hit in hits[type_]:
                msg += f'* {hit["name"]} - {hit["urls"]["view"]}\n'

        await ctx.send(msg if msg else 'Aucun résultat')

    @command_kanka.command(name="reports_channel")
    async def set_reports_channel(self, ctx: commands.Context):
        await self.config.kanka_reports_channel.set(ctx.channel.id)
        await ctx.message.add_reaction('\U00002705')  # :white_check_mark:

    # @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx = await self.bot.get_context(message)  # type: commands.Context

        if ctx.channel.id == await self.config.kanka_reports_channel() and message.author.id != ctx.me.id:
            embed = discord.Embed(description=message.content, timestamp=message.created_at)
            embed.set_author(name=f"{message.author}",
                             icon_url=message.author.avatar_url)

            bot_message = await ctx.send(None, embed=embed)
            # await self.api_client.reports.send_report(DiscordMessage(
            #     id=bot_message.id,
            #     content=str(message.clean_content),
            #     author=DiscordUser(message.author.id, message.author.name, message.author.discriminator),
            #     created_at=message.created_at.timestamp()
            # ))

            await message.delete()
            await bot_message.add_reaction("kanka:1020774086160425040")
            await bot_message.add_reaction("\U0001F5FA")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.channel_id == await self.config.kanka_reports_channel() and payload.user_id != self.bot.user.id:
            channel = self.bot.get_channel(payload.channel_id)  # type: discord.TextChannel
            message = await channel.fetch_message(payload.message_id)

            payload.__dict__.update({
                'channel': channel,
                'message': message
            })

            reaction_event = {
                'kanka': self.on_kanka_reaction,
                '🗺': self.on_map_reaction
            }.get(payload.emoji.name)

            if reaction_event:
                await reaction_event(payload)
                await message.remove_reaction(payload.emoji, payload.member)

    async def on_kanka_reaction(self, payload: RawReactionActionEvent):
        report = await self.api_client.reports.find_report_from_message(payload.message_id)
        delay = 60

        async with self.config.messages() as messages:
            if report:
                message = await payload.member.send(messages['kanka.reports.link'] % (report['url'], str(delay) + 's'))
            else:
                message = await payload.member.send(messages['kanka.reports.not_found'])

        await message.delete(delay=delay)

    async def on_map_reaction(self, payload: RawReactionActionEvent):
        report = await self.api_client.reports.find_report_from_message(payload.message_id)
        delay = 60

        await self.io.emit('location_focus', 'some location')
