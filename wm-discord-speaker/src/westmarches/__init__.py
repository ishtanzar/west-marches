from abc import ABC

from redbot.core import Config
from redbot.core.bot import Red


class MixinMeta(ABC):
    bot: Red
    config: Config
