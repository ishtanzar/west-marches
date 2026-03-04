import asyncio
import logging
import os
from asyncio import Task
from datetime import datetime
from typing import Optional, Union, List

from dateutil.relativedelta import relativedelta
from discord import TextChannel
from redbot.core import commands, checks
from westmarches_utils.config import Config
from westmarches_utils.queue import Queue, JobDefinition

from westmarches.commands import AbstractCommand

log = logging.getLogger("red.westmarches.foundry")


class FoundryCommands(AbstractCommand):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._tasks_backups: set[Task] = set()
        self._tasks_restart: set[Task] = set()
        self._delayed_restart_handle = None

    @property
    def foundry_url(self):
        return 'http://%s:5000' % os.environ['FOUNDRY_HOST']

    @property
    def foundry_auth(self):
        return 'foundry_manager', os.environ['MANAGER_API_SECRET']

    @checks.has_permissions(administrator=True)
    @commands.group(name="foundry")
    async def command_foundry(self, ctx: commands.Context):
        """Foundry admin commands"""

    @command_foundry.command(name="restart")
    async def command_restart(self, ctx: commands.Context, *args: Union[TextChannel, int, str, None]):
        """Restart FoundryVTT"""
        channel: Optional[TextChannel] = None
        delay: Optional[int] = 0
        trigger = datetime.now()

        for arg in args:
            if isinstance(arg, int):
                delay = arg
            elif isinstance(arg, TextChannel):
                channel = arg
            elif isinstance(arg, str):
                if arg == 'cancel':
                    self._tasks_restart.pop().cancel()
                    return

        if delay:
            delta = relativedelta(minutes=delay)
            trigger += delta
        else:
            delay = 0

        if channel:
            async with self.config.messages() as messages:
                await channel.send(messages['foundry.restart.notify'] % int(round(trigger.timestamp())))

        await ctx.message.add_reaction('\U0001F4C5')

        async def _do_restart():
            await asyncio.sleep(delay * 60)
            await ctx.message.add_reaction('\U000025B6')
            # await self.discord_api_wrapper(ctx, 'foundry.restart', lambda: self.wm_api.management.foundry.restart())
            await ctx.message.add_reaction('\U00002705')

        task = asyncio.create_task(_do_restart())
        self._tasks_restart.add(task)
        task.add_done_callback(self._tasks_restart.discard)

    @command_foundry.command(name="backup", invoke_without_command=True)
    async def foundry_backup(self, ctx: commands.Context, *args: List[Union[TextChannel, int, str, None]]):
        """Perform a backup of FoundryVTT. Beware that Foundry WILL BE STOPPED"""
        schemas: Optional[str] = None
        channel: Optional[TextChannel] = None
        delay: Optional[int] = 0
        trigger = datetime.now()

        for arg in args:
            if isinstance(arg, int):
                delay = arg
            elif isinstance(arg, TextChannel):
                channel = arg
            elif isinstance(arg, str):
                if arg == 'cancel':
                    self._tasks_backups.pop().cancel()
                    return
                schemas = arg

        if delay:
            delta = relativedelta(minutes=delay)
            trigger += delta

        config = Config()
        config.set('redis.endpoint', await self.config.redis.endpoint())
        queue = Queue(config)

        if channel:
            async with self.config.messages() as messages:
                await channel.send(messages['foundry.restart.notify'] % int(round(trigger.timestamp())))

        async def _do_backup():
            await asyncio.sleep(delay * 60)
            await queue.put(JobDefinition('foundry.backup',
                                          schemas=[s.strip() for s in schemas.split(',')] if schemas else ['worlds'],
                                          reaction_msg={
                                              'channel_id': ctx.channel.id,
                                              'message_id': ctx.message.id
                                          }))
            await ctx.message.add_reaction('\U0001F4C5')

        task = asyncio.create_task(_do_backup())
        self._tasks_backups.add(task)
        task.add_done_callback(self._tasks_backups.discard)
