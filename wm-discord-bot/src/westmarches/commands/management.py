import logging
from typing import List

from discord import Member, NotFound
from redbot.core import commands

from westmarches.commands import AbstractCommand


log = logging.getLogger('red.westmarches.management')


async def in_gm_guild(ctx: commands.Context):
    gm_guild_id = await ctx.cog.config.management.gm_guild()
    gm_guild = ctx.bot.get_guild(gm_guild_id)
    if gm_guild is None:
        raise commands.CheckFailure('The configured GM guild is unavailable.')
    try:
        await gm_guild.fetch_member(ctx.author.id)
    except NotFound:
        raise commands.CheckFailure('Only members of the configured GM guild can use this command.') from None
    return True



class ManagementCommands(AbstractCommand):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    # @commands.command()
    async def onboard_gm(self, ctx: commands.Context, member: Member):
        guild_id = await self.config.management.onboard.invite_guild()
        gm_guild = self.bot.get_guild(guild_id)
        players_guild = self.bot.get_guild(await self.config.management.players_guild())
        gms: List[int] = await self.config.management.gms()

        if member.id not in gms:
            gms.append(member.id)
            await self.config.management.gms.set(gms)

        if member.id not in [m.id for m in gm_guild.members]:
            channel_id = await self.config.management.onboard.invite_channel()
            invite = await self.bot.get_guild(guild_id).get_channel(channel_id).create_invite()
            await ctx.channel.send(invite.url)

        await member.add_roles(players_guild.get_role(await self.config.management.gm_role()))

    @commands.group(name='s3')
    @commands.check(in_gm_guild)
    async def group_s3(self, ctx: commands.Context):
        pass

    @group_s3.command(name='password')
    @commands.check(in_gm_guild)
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def command_s3_passwd(self, ctx: commands.Context):
        try:
            await self.s3_passwd(ctx)
        except Exception as error:
            log.error('S3 credential provisioning failed for Discord member %s (%s)',
                      ctx.author.id, type(error).__name__)
            async with self.config.messages() as messages:
                await ctx.send(messages.get(
                    'management.s3.failed',
                    "S3 credentials could not be issued. Contact an administrator before using Object Storage.",
                ))
            return
        await ctx.message.add_reaction('\U00002705')

    async def s3_passwd(self, ctx: commands.Context):
        client = self.wm_api.management.s3
        member = {
            "type": "discord",
            "discord_username": ctx.author.name,
            "discord_id": str(ctx.author.id),
        }
        credentials = await client.credentials(member)
        if not credentials.access_key or not credentials.secret_key:
            raise RuntimeError("Credential response incomplete.")
        async with self.config.messages() as messages:
            dm = await ctx.author.send(
                messages['management.s3.credentials']
                % (credentials.access_key, credentials.secret_key)
            )
        await dm.delete(delay=30)

    # @commands.command()
    async def offboard_gm(self, ctx: commands.Context, member: Member):
        gm_guild = self.bot.get_guild(await self.config.management.gm_guild())
        players_guild = self.bot.get_guild(await self.config.management.players_guild())
        gms: List[int] = await self.config.management.gms()

        if member.id in gms:
            gms.remove(member.id)
            await self.config.management.gms.set(gms)

        await gm_guild.kick(member)
        await players_guild.get_member(member.id).remove_roles(players_guild.get_role(await self.config.management.gm_role()))

    # @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        gm_guild = self.bot.get_guild(await self.config.management.onboard.invite_guild())
        if member.guild.id == gm_guild.id and member.id in await self.config.management.gms():
            await member.add_roles(gm_guild.get_role(await self.config.management.gm_role()))
