from westmarches_utils.api import AbstractApi


class IntentsApi(AbstractApi):

    async def add_pattern(self, intent, pattern) -> None:
        await self.post('/intent/%s/pattern' % intent, json={
            'pattern': pattern
        })

    async def train(self) -> None:
        await self.post('/intent/train')

    async def predict(self, message) -> dict:
        resp = await self.post('/intent/predict', json={
            'message': message
        })
        return resp.json()
