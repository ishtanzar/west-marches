import dataclasses

from westmarches_utils.api import AbstractApi
from westmarches_utils.api.discord import DiscordMessage


class ReportsApi(AbstractApi):

    async def send_report(self, message: DiscordMessage):
        resp = await self.post('/report/discord', json=dataclasses.asdict(message))
        return resp.json()

    async def find_report_from_message(self, message_id):
        resp = await self.get('/report/discord/%s' % message_id)
        return next(iter(resp.json()['reports']), None)
