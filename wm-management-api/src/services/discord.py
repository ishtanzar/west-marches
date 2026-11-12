import logging
from typing import NoReturn

import discord
from werkzeug.exceptions import BadRequest, Forbidden, ServiceUnavailable


class DiscordError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

    def to_http_error(self) -> NoReturn:
        if self.code in {"invalid_discord_id", "invalid_discord_username"}:
            raise BadRequest(self.code) from None
        if self.code in {"not_current_gm", "identity_mismatch"}:
            raise Forbidden(self.code) from None
        raise ServiceUnavailable(self.code) from None


def snowflake(value):
    raw = str(value)
    if isinstance(value, bool) or len(raw) > 20 or not raw.isdigit() or not 0 < int(raw) < 2**64:
        raise DiscordError("invalid_discord_id")
    return str(int(raw))


class DiscordService:
    @staticmethod
    def validate_member(member_id, username):
        if not isinstance(username, str) or not username.strip() or len(username) > 256:
            raise DiscordError("invalid_discord_username")
        return username, snowflake(member_id)

    def __init__(self, token, guild_id, bot_id):
        self.token = token
        self.guild_id = snowflake(guild_id)
        self.bot_id = snowflake(bot_id)
        self.client = discord.Client(intents=discord.Intents.none())
        logging.getLogger("discord.http").setLevel(logging.WARNING)

    async def start(self):
        await self.client.login(self.token)
        identity = self.client.user
        if identity is None or str(identity.id) != self.bot_id or not identity.bot:
            raise DiscordError("discord_bot_configuration")

    async def close(self):
        await self.client.close()

    async def member(self, member_id):
        member_id = snowflake(member_id)
        try:
            guild = await self.client.fetch_guild(int(self.guild_id))
        except discord.HTTPException:
            raise DiscordError("discord_unavailable") from None
        if str(guild.id) != self.guild_id:
            raise DiscordError("discord_unavailable")
        try:
            member = await guild.fetch_member(int(member_id))
        except discord.NotFound as error:
            if error.status != 404 or error.code != 10007:
                raise DiscordError("discord_unavailable") from None
            member = None
        except discord.HTTPException:
            raise DiscordError("discord_unavailable") from None
        if member is None or member.bot:
            raise DiscordError("not_current_gm")
        if str(member.id) != member_id or not isinstance(member.name, str):
            raise DiscordError("identity_mismatch")
        return member.name
