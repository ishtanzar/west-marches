import logging.config
import os

import yaml
from discord.ext.commands import Context
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from . import commands
from .api import WestMarchesApiClient, BasicAuth, HTTPException
from .utils import CompositeMetaClass, log_message


class WestMarchesCog(commands.Commands,
                     Cog,
                     metaclass=CompositeMetaClass):
    default_guild_settings = {
        "rumors": [],
        "rumors_idx": 0,
        "rumors_triggers": {},
        "rumors_cooldown_message": [
            "On se calme, repasses plus tard.",
            "Hey, je suis pas un robot.",
            "J'ai d'autres choses à faire que de discuter."
        ],
        "intents": [],
        "taverns": [],
        "messages": {
            "intents.learn.done": "On en apprend de belles tous les jours !",
            "intents.train.done": "Rien de tel qu'une bonne scéance d'entraînement pour garder la forme.",
            "sessions.schedule.done": "Rapport créé : {}. Bonne partie !",

            "foundry.backup.started": "Bon allez, tout le monde dehors, on ferme la taverne pour ce soir.",
            "foundry.backup.failed": "La porte de la réserve est restée coincée, on a pas rangé la dernière livraison",
            "foundry.backup.done": "C'est bon, on a pu ranger la réserve, on peut ouvrir pour la journée !",

            "foundry.restart.started": "Krusk, ça sent encore le cramé; ouvre la fenêtre !",
            "foundry.restart.done": "Merci",

            "foundry.backup_restore.started": "Ce tonneau de bière sent le rance, "
                                              "faut en prendre un autre dans la réserve",
            "foundry.backup_restore.failed": "Pas moyen de trouver un bon tonneau de secours.",
            "foundry.backup_restore.done": "Voilà, on a récupéré un bon tonneau; ça devrait aller mieux",

            "foundry.roster.intro": "*%s déroule une feuille de parchemin vierge sur la table entre vous et pose une "
                                    "pierre dont émane une étrange aura magique. Alors que la pierre touche le "
                                    "parchemin, une étrange liste de noms apparaît.*",
            "foundry.roster.search.class": "Parmis les aventuriers qui viennent ici, voici les %s que je connais : %s",

            "foundry.player.add.done": "Bienvenue parmis nous %s. Puisses-tu survivre longtemps sur ces terres gelées.",
            "foundry.player.discord.not_found": "Aucune correspondance sur Foundry pour l'utilisateur %s.",
            "foundry.player.password.reset": "Le mot de passe Foundry a été réinitialisé : %s",
            "foundry.player.toggle_gm.activate": "%s est maintenant MJ.",
            "foundry.player.toggle_gm.deactivate": "%s n'est plus MJ.",
            "foundry.activity.users": "Utilisateurs connectés : %s.",
            "inkarnate.password": "%s\nCe message sera automatiquement supprimé dans 30s.",
            "gm.message.sent": "Ton message a bien été transmis, l'équipe en discute et reviendra vers toi par message "
                               "privé. Bonne journée.",
        }
    }

    def __init__(self, bot: Red):
        super().__init__()

        self.bot = bot
        self.setup_events()

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**self.default_guild_settings)

        if 'LOGGING_CONFIG' in os.environ.keys():
            self.setup_logging()

        api_auth = BasicAuth('foundry_manager', os.environ['WM_API_SECRET'])
        self.api_client = WestMarchesApiClient(api_auth, os.environ['WM_API_ENDPOINT'])

    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        async with self.config.messages() as _messages:
            messages = _messages

        try:
            await ctx.send(messages[messages_key + '.started'])
            await f()
            await ctx.send(messages[messages_key + '.done'])
        except HTTPException:
            await ctx.send(messages[messages_key + '.failed'])

    @staticmethod
    def setup_logging():
        config = {}
        with open(os.environ['LOGGING_CONFIG']) as fd:
            config = yaml.safe_load(fd.read())

        logging.config.dictConfig(config)

    def setup_events(self):
        @self.bot.event
        async def on_command(ctx: Context):
            log_message(ctx)
