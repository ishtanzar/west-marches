from typing import Optional

import asyncio


class JobDefinition:

    def __init__(self, handler: str, job_args: Optional[list] = None, job_kwargs: Optional[dict] = None):
        self._handler = handler
        self._args = job_args
        self._kwargs = job_kwargs

    @property
    def handler(self):
        return self._handler

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs


class Job:
    def __init__(self, definition: JobDefinition, handler):
        self._definition = definition
        self._handler = handler

    async def run(self):
        _args = self._definition.args
        _kwargs = self._definition.kwargs

        return await self._handler(
            *_args if _args is not None else [],
            **_kwargs if _kwargs is not None else {}
        )

class Queue:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._routines = {}

    async def put(self, job):
        await self._queue.put(job)

    async def get(self):
        job_def = await self._queue.get()
        return Job(job_def, self._routines[job_def.handler] if job_def.handler in self._routines else None)

    def register(self, key, routine):
        self._routines[key] = routine
