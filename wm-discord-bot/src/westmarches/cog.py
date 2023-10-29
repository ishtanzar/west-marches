import logging.config
import os

import socketio
from redbot.core.commands import Cog
from westmarches_utils.api.auth import Basic, APIKey
from westmarches_utils.api.config import WestMarchesApiConfig

from .commands import *
from .utils import log_message

log = logging.getLogger('red.westmarches')

class Commands(
    FoundryCommands,
    InkarnateCommands,
    KankaCommands,
    Forward,
    ManagementCommands,
    SessionsCommands):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class WestMarchesCog(Commands):

    def __init__(self, bot: Red, io: socketio.AsyncClient, config: dict):
        super(Cog, self).__init__()

        self.bot = bot
        self.io = io
        self.es = Elasticsearch('http://elasticsearch:9200')

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**config)

        # noinspection PyArgumentList
        super(Commands, self).__init__()

        self.setup_events()

        api_config = WestMarchesApiConfig(
            api_auth=APIKey(os.environ['API_TOKEN']),
            management_api_auth=Basic('foundry_manager', os.environ['MGMNT_API_SECRET'])
        )

        self.wm_api = WestMarchesApi(api_config)

        log.info("WestMarches loaded")

    def setup_events(self):
        @self.bot.event
        async def on_command(ctx: Context):
            log_message(ctx)
