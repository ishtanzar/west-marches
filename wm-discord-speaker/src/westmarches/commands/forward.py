import discord
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta


class Forward(MixinMeta, metaclass=CompositeMetaClass):

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
        channel = await self.config.destination()
        channel = self.bot.get_channel(channel)
        if channel is None:
            await self.bot.send_to_owners(msg, embed=embed)
        else:
            await channel.send(msg, embed=embed)

    @commands.command()
    async def gm(self, ctx: commands.Context):
        embeds = [discord.Embed(description=ctx.message.content.replace(ctx.prefix + '' + ctx.invoked_with, ''))]
        embeds[0].set_author(name=f"{ctx.message.author} | {ctx.message.author.id}", icon_url=ctx.message.author.avatar_url)
        embeds = self._append_attachements(ctx.message, embeds)
        embeds[-1].timestamp = ctx.message.created_at

        await self.bot.wait_until_ready()
        channel = await self.config.destination()
        channel = self.bot.get_channel(channel)

        if channel is None:
            for embed in embeds:
                await self.bot.send_to_owners(None, embed=embed)
        else:
            lines = embeds.pop(0).description.splitlines()
            async with self.config.messages() as messages:
                thread = await channel.create_thread(
                    messages['gm.message.title'] % (
                        ctx.message.author,
                        lines[0] if len(lines) > 1 else messages['gm.message.title.default']
                    ),
                    '\n'.join(lines[1:] if len(lines) > 1 else lines)
                )
            for embed in embeds:
                await thread.send(embed=embed)

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
        await self.config.destination.set(data["config"])
        await ctx.send(data["msg"])
