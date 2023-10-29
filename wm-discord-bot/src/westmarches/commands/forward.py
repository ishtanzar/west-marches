import logging

import discord
from redbot.core import commands, checks

from westmarches.commands import AbstractCommand

log = logging.getLogger("red.westmarches.forward")

class Forward(AbstractCommand):

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

    async def _destination(self, msg: str = None, embed: discord.Embed = None):
        await self.bot.wait_until_ready()
        channel = await self.config.forward.destination()
        channel = self.bot.get_channel(channel)
        if channel is None:
            await self.bot.send_to_owners(msg, embed=embed)
        else:
            await channel.send(msg, embed=embed)

    @commands.command()
    async def gm(self, ctx: commands.Context):
        embeds = [discord.Embed(description=ctx.message.content.replace(ctx.prefix + '' + ctx.invoked_with, ''))]
        embeds[0].set_author(name=f"{ctx.message.author} | {ctx.message.author.id}", icon_url=ctx.message.author.avatar.url)
        embeds = self._append_attachements(ctx.message, embeds)
        embeds[-1].timestamp = ctx.message.created_at
        for embed in embeds:
            await self._destination(msg=None, embed=embed)

        async with self.config.messages() as messages:
            await ctx.send(messages['gm.message.sent'])

    @checks.has_permissions(administrator=True)
    @commands.command()
    async def gm_setforward(self, ctx, channel: discord.TextChannel = None):
        """Set if you want to receive notifications in a channel instead of your DMs.
        Leave blank if you want to set back to your DMs.
        """
        data = (
            {"msg": "Notifications will be sent in your DMs.", "config": None}
            if channel is None
            else {"msg": f"Notifications will be sent in {channel.mention}.", "config": channel.id}
        )
        await self.config.forward.destination.set(data["config"])
        await ctx.send(data["msg"])

    @commands.Cog.listener('on_message_without_command')
    async def on_question_thread_message(self, message):
        if isinstance(message.channel, discord.Thread) and \
                message.channel.parent_id == await self.config.forward.questions_channel() and message.content == '✅':
                log.info(f"Question is considered answered, closing the thread")
                await message.channel.send('Ce sujet est désormais clos, merci.')
                log.debug('Fetching original message')
                original_message = await self._get_thread_original_message(message.channel)
                log.debug('Fetching full original message')
                full_message = await message.channel.parent.fetch_message(original_message.id)
                log.debug('Adding reaction')
                await full_message.add_reaction('✅')
                log.debug('Archiving thread')
                await message.channel.edit(archived=True)
        
    @commands.Cog.listener('on_message_without_command')
    async def forward_on_message_without_command(self, message):
        ctx: commands.Context = await self.bot.get_context(message)
        gm_guild = self.bot.get_guild(await self.config.management.gm_guild())

        if isinstance(message.channel, discord.Thread):
            notif_channel = None
            if message.channel.parent_id == await self.config.forward.downtime_channel():
                notif_channel = gm_guild.get_channel_or_thread(await self.config.forward.downtime_notif_channel())

            if message.channel.parent_id == await self.config.forward.character_sheet_channel():
                notif_channel = gm_guild.get_channel_or_thread(await self.config.forward.character_sheet_notif_channel())

            if notif_channel:
                embeds = [discord.Embed(title=message.channel.name, description=message.content, url=message.channel.jump_url)]
                embeds[0].set_author(name=f"{message.author} | {message.author.id}", icon_url=message.author.avatar.url)
                embeds = self._append_attachements(message, embeds)
                embeds[-1].timestamp = message.created_at

                for embed in embeds:
                    await notif_channel.send(None, embed=embed)
