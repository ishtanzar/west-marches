from typing import Optional

from westmarches_utils.api import AbstractApi


class FoundryApi(AbstractApi):

    async def backup(self) -> None:
        await self.post('/backup/perform')

    async def list_backups(self) -> dict:
        resp = await self.get('/backup/list')
        return resp.json()

    async def restore(self, backup_id: str) -> None:
        await self.post('/backup/restore/%s' % backup_id)

    async def restart(self) -> None:
        await self.post('/foundry/restart')

    async def actors(self) -> dict:
        resp = await self.search('/foundry/actors')
        return resp.json()

    async def users(self, filter: Optional[object] = None):
        resp = await self.search('/foundry/users', json=filter)
        return resp.json()

    async def users_add(self, name, discord: Optional[object] = None) -> str:
        resp = await self.post('/foundry/users', json={
            'name': name,
            'discord': discord
        })
        return resp.json()

    async def users_update(self, user_id, name: Optional[str] = None, role: Optional[int] = None,
                           password: Optional[str] = None, discord: Optional[object] = None) -> str:
        body = {}
        if name:
            body['name'] = name
        if role:
            body['role'] = role
        if password:
            body['password'] = password
        if discord:
            body['discord'] = discord

        resp = await self.put('/foundry/users/%s' % user_id, json=body)
        return resp.json()

    async def activity(self) -> dict:
        resp = await self.get('/foundry/activity')
        return resp.json()
