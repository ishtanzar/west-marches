import json

from discord import Guild

from storage import ReplitDBStorable


class Integration(ReplitDBStorable):

    @staticmethod
    def prefix():
        return 'integration/'

    @staticmethod
    def from_json(json_obj):
        if json_obj:
            obj = json.loads(json_obj)
            result = Integration()
            result.guild_id = obj['guild_id']

            return result

    def __init__(self):
        self.guild_id = None

    def join(self, guild: Guild) -> 'Integration':
        self.guild_id = guild.id
        return self

    def key(self):
        return Integration.prefix() + self.guild_id

    def to_json(self):
        return json.dumps({
            'guild_id': self.guild_id
        })
