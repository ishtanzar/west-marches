import json
import redis.asyncio as redis


class JobDefinition:

    def __init__(self, handler: str, *args, **kwargs):
        self._handler = handler
        self._args = args if args else []
        self._kwargs = kwargs if kwargs else {}

    @property
    def handler(self):
        return self._handler

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def to_json(self):
        return json.dumps({
            'handler': self.handler,
            'args': self.args,
            'kwargs': self.kwargs
        })

    @classmethod
    def from_json(cls, json_def: str):
        dict_def = json.loads(json_def)
        return JobDefinition(
            dict_def['handler'],
            *dict_def['args'] if 'args' in dict_def else [],
            **dict_def['kwargs'] if 'kwargs' in dict_def else {}
        )


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
    def __init__(self, config):
        self._config = config
        self._redis = redis.Redis.from_url(config.redis.endpoint)
        self._queue = 'wm-worker-queue'
        self._routines = {}

    async def put(self, job: JobDefinition):
        await self._redis.lpush(self._queue, job.to_json())

    async def get(self):
        _, json_def = await self._redis.brpop(self._queue)
        job_def = JobDefinition.from_json(json_def)
        return Job(job_def, self._routines[job_def.handler] if job_def.handler in self._routines else None)

    def register(self, key, routine):
        self._routines[key] = routine
