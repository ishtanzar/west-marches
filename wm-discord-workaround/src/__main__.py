import json
import logging.config
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Any, Type
from discord.ext import commands

import discord
from discord.ext.commands import Context
from discord.ext.commands._types import BotT


# from westmarches.api import BasicAuth, WestMarchesApiClient, DiscordMessage, DiscordUser


class Config:
    __data__ = object()

    @staticmethod
    def get():
        return Config.__data__

    @staticmethod
    def load(path):
        with Path(path).open() as fp:
            Config.__data__ = json.load(fp, object_hook=lambda x: SimpleNamespace(**x))
        return Config.__data__


class PlayerReport(discord.ui.View):
    def __init__(self, kanka_url: str):
        super().__init__()

        self.add_item(discord.ui.Button(emoji='kanka:1020774086160425040', url=kanka_url))
        self.add_item(discord.ui.Button(emoji="\U0001F5FA", custom_id='map_fly_to'))


class PlayerReportConfirm(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(discord.ui.Button(label='Yes', custom_id='map_set_location'))
        self.add_item(discord.ui.Button(label='No', custom_id='generic_cancel'))


class WorkaroundCog(commands.Cog):

    def __init__(self, config: Config, bot: commands.Bot) -> None:
        self._config = config
        self._bot = bot
        self._logger = logging.getLogger('cog')

    async def _get_thread_original_message(self, channel: discord.Thread):
        try:
            async for starter_message in channel.history(limit=1, oldest_first=True):
                if starter_message.type is discord.MessageType.thread_starter_message:
                    return starter_message.reference.resolved
        except Exception as e:
            self._logger.warning(str(e), exc_info=True)

    async def _get_thread_original_message_mentions(self, channel: discord.Thread, guild: discord.Guild):
        members = []
        original_message = await self._get_thread_original_message(channel)

        for user in original_message.mentions:
            members.append((await guild.query_members(user_ids=[user.id]))[0])

        return members

    @staticmethod
    def _append_attachements(message: discord.Message, embeds: list):
        attachments_urls = []
        for attachment in message.attachments:
            if any(attachment.filename.endswith(imageext) for imageext in ["jpg", "png", "gif"]):
                if embeds[0].image:
                    embed = discord.Embed()
                    embed.set_image(url=attachment.url)
                    embeds.append(embed)
                else:
                    embeds[0].set_image(url=attachment.url)
            else:
                attachments_urls.append(f"[{attachment.filename}]({attachment.url})")
        if attachments_urls:
            embeds[0].add_field(name="Attachments", value="\n".join(attachments_urls))
        return embeds

    async def cog_command_error(self, ctx: Context[BotT], error: Exception) -> None:
        self._logger.warning(str(error), exc_info=True)

    async def cog_before_invoke(self, ctx: Context[BotT]) -> None:
        self._logger.info(f'{ctx.author.name}#{ctx.author.discriminator}: {ctx.message.content}')

    @commands.command(name="session")
    async def session_start(self, ctx: commands.Context):
        if ctx.author.get_role(self._config.discord.gm_role):
            if isinstance(ctx.channel, discord.Thread):
                gm_guild = self._bot.get_guild(self._config.discord.gm_guild)
                session_role = ctx.guild.get_role(self._config.discord.session_role)
                thread_message = "Début de session pour :\n"
                gm_notif = f"Session de {ctx.author.name} avec :\n"

                for member in await self._get_thread_original_message_mentions(ctx.channel, ctx.guild):
                    await member.add_roles(session_role)
                    thread_message += f'- {member.mention}\n'
                    gm_notif += f'- {member.name}\n'

                notif_channel = gm_guild.get_channel_or_thread(self._config.discord.session_notif_channel)
                await notif_channel.send(gm_notif)
                await ctx.channel.send(thread_message)
            else:
                await ctx.send('Not implemented yet')
        else:
            await ctx.send("Tu t'es pris pour un MJ ?")

    @commands.command()
    async def session_end(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.Thread):
            session_role = ctx.guild.get_role(self._config.discord.session_role)

            for member in await self._get_thread_original_message_mentions(ctx.channel, ctx.guild):
                await member.remove_roles(session_role)

            await ctx.channel.send("Fin de session.")
        else:
            self._logger.warning('session_end not in a thread')

    @commands.Cog.listener()
    async def on_raw_thread_update(self, payload: discord.RawThreadUpdateEvent):
        if payload.thread and payload.thread.archived:
            if payload.parent_id == self._config.discord.questions_channel:
                self._logger.info(f"Thread '{payload.thread.name}' is archiving, checking for status")
                original_message = await self._get_thread_original_message(payload.thread)
                if original_message:
                    full_message = await payload.thread.parent.fetch_message(original_message.id)

                    for reaction in full_message.reactions:
                        if reaction.emoji == '✅':
                            self._logger.info("Question has check emoji, let it archived")
                            return

                    self._logger.info("Question do not have the check emoji, stay open")
                    await payload.thread.edit(archived=False)

            if payload.parent_id == self._config.discord.downtime_channel:
                self._logger.info(f"Downtime thread '{payload.thread.name}' is archiving, keeping it opened")
                await payload.thread.edit(archived=False)

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author == self._bot.user:
            return

        # if message.channel.id == 859433172704690186:
        #     embed = discord.Embed(description=message.content, timestamp=message.created_at)
        #     embed.set_author(name=f"{message.author}",
        #                      icon_url=message.author.avatar.url)
        #
        #     bot_message = await message.channel.send(None, embed=embed)
        #
        #     report = await api_client.reports.send_report(DiscordMessage(
        #         id=bot_message.id,
        #         content=str(message.clean_content),
        #         author=DiscordUser(message.author.id, message.author.name, message.author.discriminator),
        #         created_at=message.created_at.timestamp()
        #     ))
        #
        #     await bot_message.edit(view=PlayerReport(f"https://kanka.io/fr/campaign/93396/journals/{report['id']}"))
        #
        #     confirm = await message.channel.send(f'{message.author.mention}, merci pour ton rapport. Est-ce que tu '
        #                                          f'souhaites indiquer un emplacement en lien sur la carte des joueurs ?',
        #                                          view=PlayerReportConfirm())
        #
        #     await message.delete()

        if isinstance(message.channel, discord.Thread):
            if message.channel.parent_id == self._config.discord.questions_channel and message.content == '✅':
                self._logger.info(f"Question is considered answered, closing the thread")
                await message.channel.send('Ce sujet est désormais clos, merci.')
                self._logger.debug('Fetching original message')
                original_message = await self._get_thread_original_message(message.channel)
                self._logger.debug('Fetching full original message')
                full_message = await message.channel.parent.fetch_message(original_message.id)
                self._logger.debug('Adding reaction')
                await full_message.add_reaction('✅')
                self._logger.debug('Archiving thread')
                await message.channel.edit(archived=True)

            if message.channel.parent_id == self._config.discord.downtime_channel:
                gm_guild = self._bot.get_guild(self._config.discord.gm_guild)
                notif_channel = gm_guild.get_channel_or_thread(self._config.discord.downtime_notif_channel)

                embeds = [discord.Embed(title=message.channel.name, description=message.content, url=message.channel.jump_url)]
                embeds[0].set_author(name=f"{message.author} | {message.author.id}", icon_url=message.author.avatar.url)
                embeds = self._append_attachements(message, embeds)
                embeds[-1].timestamp = message.created_at

                for embed in embeds:
                    await notif_channel.send(None, embed=embed)


class WorkaroundBot(commands.Bot):

    def __init__(self, config, **options: Any) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        self._config = config
        self._logger = logging.getLogger('bot')
        self._cog = WorkaroundCog(config, self)

        super().__init__(command_prefix=commands.when_mentioned, intents=intents, **options)

    async def on_ready(self):
        self._logger.info(f'We have logged in as {self.user}')

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(f'Error in {event_method}', exc_info=True)

    async def setup_hook(self) -> None:
        await self.add_cog(self._cog)

    async def process_commands(self, message: discord.Message, /):
        """
        Same as base method, but dispatches an additional event for cogs
        which want to handle normal messages differently to command
        messages,  without the overhead of additional get_context calls
        per cog.
        """
        if not message.author.bot:
            ctx = await self.get_context(message)
            if ctx.invoked_with and isinstance(message.channel, discord.PartialMessageable):
                self._logger.warning(
                    "Discarded a command message (ID: %s) with PartialMessageable channel: %r",
                    message.id,
                    message.channel,
                )
            else:
                await self.invoke(ctx)
        else:
            ctx = None

        if ctx is None or ctx.valid is False:
            self.dispatch("message_without_command", message)


def main():
    config = Config.load(os.environ.get('CONFIG_PATH', '/etc/wm-worker/config.json'))
    config.discord.token = os.environ.get('DISCORD_BOT_SECRET', config.discord.token)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    # Ugly SN to dict converted
    logging.config.dictConfig(json.loads(json.dumps(config.log, default=lambda x: vars(x))))

    bot = WorkaroundBot(config)

    # api_auth = BasicAuth('foundry_manager', os.environ['WM_API_SECRET'])
    # api_client = WestMarchesApiClient(api_auth, os.environ['WM_API_ENDPOINT'])

    bot.run(config.discord.token)


if __name__ == "__main__":
    main()


