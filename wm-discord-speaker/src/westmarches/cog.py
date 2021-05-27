import spacy
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from . import commands
from .utils import CompositeMetaClass


class WestMarchesCog(commands.Commands,
                     Cog,
                     metaclass=CompositeMetaClass):

    default_guild_settings = {
        "rumors": [],
        "intents": []
    }

    def __init__(self, bot: Red):
        super().__init__()

        self.bot = bot
        self.nlp = spacy.load('fr_core_news_sm')

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**self.default_guild_settings)
