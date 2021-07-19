import logging
import re

import discord
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta, log_message

PUNCTUATION = list("?:!.,;")
log = logging.getLogger("red.westmarches.chatbot")


class ChatbotCommands(MixinMeta, metaclass=CompositeMetaClass):

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx = await self.bot.get_context(message)  # type: commands.Context

        if str(self.bot.user.id) in message.content:
            log_message(ctx)
            clean_message = re.sub('<@!?([0-9]*)>', '', message.content)
            async with ctx.typing():
                resp = await self.api_client.intents.predict(clean_message)
                intent = resp['prediction']

            if intent == "rumors":
                await self.bot.all_commands.get("rumors").invoke(ctx)
            elif intent == "greeting":
                await ctx.send("Bonjour")
            else:
                await ctx.send(intent)

    @checks.is_owner()
    @commands.command()
    async def learn(self, ctx: commands.Context, new_intent):
        """Learn an intent from a message"""
        async with ctx.typing():
            if ctx.message.reference:
                message = await ctx.fetch_message(ctx.message.reference.message_id)
                clean_message = re.sub('<@!?([0-9]*)>', '', message.content).strip()
                await self.api_client.intents.add_pattern(new_intent, clean_message)

        async with self.config.messages() as messages:
            await ctx.send(messages['intents.learn.done'])

    @checks.is_owner()
    @commands.command()
    async def train(self, ctx: commands.Context):
        """Update AI model"""
        async with ctx.typing():
            await self.api_client.intents.train()

        async with self.config.messages() as messages:
            await ctx.send(messages['intents.train.done'])
