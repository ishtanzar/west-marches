import discord
from discord import Thread
from redbot.core import commands

from westmarches.commands import AbstractCommand


class SessionsCommands(AbstractCommand):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @commands.command(name="session")
    async def session_start(self, ctx: commands.Context):
        if ctx.author.get_role(await self.config.management.gm_role()):
            if isinstance(ctx.channel, Thread):
                gm_guild = self.bot.get_guild(await self.config.management.gm_guild())
                session_role = ctx.guild.get_role(await self.config.management.session_role())
                thread_message = "Début de session pour :\n"
                gm_notif = f"Session de {ctx.author.name} avec :\n"

                for member in await self._get_thread_original_message_mentions(ctx.channel, ctx.guild):
                    await member.add_roles(session_role)
                    thread_message += f'- {member.mention}\n'
                    gm_notif += f'- {member.name}\n'

                notif_channel = gm_guild.get_channel_or_thread(await self.config.sessions.session_notif_channel())
                await notif_channel.send(gm_notif)
                await ctx.channel.send(thread_message)
            else:
                await ctx.send('Not implemented yet')
        else:
            await ctx.send("Tu t'es pris pour un MJ ?")

    @commands.command()
    async def session_end(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.Thread):
            session_role = ctx.guild.get_role(await self.config.management.session_role())

            for member in await self._get_thread_original_message_mentions(ctx.channel, ctx.guild):
                await member.remove_roles(session_role)

            await ctx.channel.send("Fin de session.")
