from asyncio import Queue
from uuid import UUID

from services.database import Engine, Task


class TaskService:

    def __init__(self, engine: type[Engine]) -> None:
        self._queue = Queue()
        self.Engine = engine

    async def put(self, task: Task) -> UUID:
        task.insert()
        await self._queue.put(task.id)

        return task.id

    async def pop(self) -> Task:
        key = await self._queue.get()
        return self.Engine.tasks().find_one(key)
