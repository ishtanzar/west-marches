import spacy
from discord.ext.commands import Context
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from . import commands
from .utils import CompositeMetaClass, log_message


class WestMarchesCog(commands.Commands,
                     Cog,
                     metaclass=CompositeMetaClass):
    default_guild_settings = {
        "rumors": [],
        "intents": [],
        "taverns": []
    }

    def __init__(self, bot: Red):
        super().__init__()

        self.bot = bot
        self.setup_events()

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**self.default_guild_settings)

        self.nlp = spacy.load('fr_core_news_sm')

    def setup_events(self):
        @self.bot.event
        async def on_command(ctx: Context):
            log_message(ctx)
