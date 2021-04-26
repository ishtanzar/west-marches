import os
import discord

from keep_alive import keep_alive

client = discord.Client()

@client.event
async def on_ready():
    print("I'm in")
    print(client.user)

@client.event
async def on_message(message):
  if isinstance(message.channel, discord.DMChannel):
    await client.get_channel(830313964495831090).send(message.content)

keep_alive()
token = os.environ.get("DISCORD_BOT_SECRET")
client.run(token)