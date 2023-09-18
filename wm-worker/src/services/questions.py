import discord
import logging


class Questions:

    def __init__(self, config, discord: discord.Client):
        self._logger = logging.getLogger(type(self).__name__)
        self._discord = discord
        self._config = config

    async def review(self):
        channel = await self._discord.fetch_channel(self._config.discord.questions_channel)
        threads = channel.threads
        self._logger.debug(f'Found {len(threads)} threads to review')
        for thread in threads:
            resolved = False
            self._logger.debug(f'Reviewing thread named "{thread.name}"')
            async for starter_message in thread.history(limit=1, oldest_first=True):
                if starter_message.type is discord.MessageType.thread_starter_message:
                    full_message = await channel.fetch_message(starter_message.reference.resolved.id)
                    for reaction in full_message.reactions:
                        if reaction.emoji == '✅':
                            self._logger.debug("Question has check emoji, don't update it")
                            resolved = True
                            break
            if not resolved:
                self._logger.debug(f'Thread named "{thread.name}" is not resolved, updating.')
                update_message = await thread.send('.')
                await update_message.delete(delay=2)

    async def cron(self):
        self._logger.info('Review opened questions')
        await self.review()
