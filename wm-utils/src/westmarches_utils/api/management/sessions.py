from westmarches_utils.api import AbstractApi


class SessionApi(AbstractApi):

    async def schedule(self, date: str, message: dict) -> dict:
        resp = await self.post('/session', json={
            'date': date,
            'message': message,
        })
        return resp.json()
