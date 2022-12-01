import discord
from discord import TextChannel, Message, Client


class DiscordService:

    def __init__(self, secret: str) -> None:
        super().__init__()

        self._secret = secret
        self._connected = False
        self._client: Client = discord.Client()

    async def setup(self):
        await self._client.login(self._secret, bot=True)
        self._connected = True

    async def fetch_message(self, channel_id, message_id) -> Message:
        if not self._connected:
            await self.setup()

        channel: TextChannel = await self._client.fetch_channel(channel_id)
        return await channel.fetch_message(message_id)
