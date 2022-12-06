import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Any, Type
from discord.ext import commands

import discord

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

    def __init__(self, config: Config) -> None:
        self._config = config

    @staticmethod
    async def get_thread_original_message_mentions(channel: discord.Thread, guild: discord.Guild):
        members = []

        async for starter_message in channel.history(limit=1, oldest_first=True):
            if starter_message.type is discord.MessageType.thread_starter_message:
                original_message = starter_message.reference.resolved

                for user in original_message.mentions:
                    members.append((await guild.query_members(user_ids=[user.id]))[0])

                return members

    @commands.command(name="session")
    async def session_start(self, ctx: commands.Context):
        if ctx.author.get_role(self._config.discord.gm_role):
            if isinstance(ctx.channel, discord.Thread):
                session_role = ctx.guild.get_role(self._config.discord.session_role)
                thread_message = "Début de session pour :\n"
                gm_notif = f"Session de {ctx.author.name} avec :\n"

                for member in await self.get_thread_original_message_mentions(ctx.channel, ctx.guild):
                    await member.add_roles(session_role)
                    thread_message += f'- {member.mention}\n'
                    gm_notif += f'- {member.name}\n'

                notif_channel = await ctx.guild.fetch_channel(self._config.discord.session_notif_channel)
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

            for member in await self.get_thread_original_message_mentions(ctx.channel, ctx.guild):
                await member.remove_roles(session_role)

            await ctx.channel.send("Fin de session.")
        else:
            pass


class WorkaroundBot(commands.Bot):

    def __init__(self, config, **options: Any) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        self._config = config

        super().__init__(command_prefix=commands.when_mentioned, intents=intents, **options)

    async def on_ready(self):
        print(f'We have logged in as {self.user}')

    async def setup_hook(self) -> None:
        await self.add_cog(WorkaroundCog(self._config))

    # async def on_message(self, message: discord.Message):
    #     if message.author != self.user:
    #         pass
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


def main():
    config = Config.load(os.environ.get('CONFIG_PATH', '/etc/wm-worker/config.json'))
    config.discord.token = os.environ.get('DISCORD_BOT_SECRET', config.discord.token)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    bot = WorkaroundBot(config)

    # api_auth = BasicAuth('foundry_manager', os.environ['WM_API_SECRET'])
    # api_client = WestMarchesApiClient(api_auth, os.environ['WM_API_ENDPOINT'])

    bot.run(config.discord.token)


if __name__ == "__main__":
    main()


