import boto3
from abc import abstractmethod
from discord import Member
from redbot.core import commands

from westmarches.utils import MixinMeta, CompositeMetaClass


class ManagementCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: commands.Context, messages_key: str, f):
        pass

    @commands.group(name='s3')
    async def group_s3(self, ctx: commands.Context):
        pass

    @group_s3.command(name='password')
    async def command_s3_passwd(self, ctx: commands.Context):
        await self.s3_passwd(ctx.author)
        await ctx.message.add_reaction('\U00002705')

    async def s3_passwd(self, member: Member):
        iam = boto3.client('iam')
        iam_user = None

        username = member.name
        for u in iam.list_users()['Users']:
            if username == u['UserName']:
                iam_user = u

        if not iam_user:
            iam.create_user(
                Path='/westmarches_du_cairne/',
                UserName=username
            )

        iam_group = 'caveduroliste-westmarches-admins'
        if iam_group not in [g['GroupName'] for g in iam.list_groups_for_user(UserName=username)['Groups']]:
            iam.add_user_to_group(GroupName=iam_group, UserName=username)

        for iam_key in iam.list_access_keys(UserName=username)['AccessKeyMetadata']:
            iam.delete_access_key(
                UserName=username,
                AccessKeyId=iam_key['AccessKeyId']
            )

        iam_key = iam.create_access_key(UserName=username)['AccessKey']
        async with self.config.messages() as messages:
            await member.send(
                messages['management.s3.credentials'] % (iam_key['AccessKeyId'], iam_key['SecretAccessKey']),
                delete_after=30
            )

