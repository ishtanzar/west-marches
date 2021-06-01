from redbot.core.bot import Red

from .cog import WestMarchesCog


def setup(bot: Red):
    bot.add_cog(WestMarchesCog(bot))
