import asyncio
import functools
import logging
import os
import sys
from argparse import Namespace

from redbot.__main__ import global_exception_handler, run_bot, red_exception_handler, shutdown_handler
from redbot.cogs.permissions import setup as permissions
from redbot.core import data_manager
from redbot.core.bot import RedBase, ExitCodes

from westmarches.cog import WestMarchesCog


class _DefaultRepr:
    def __repr__(self):
        return '<default-help-command>'


_default = _DefaultRepr()
log = logging.getLogger("red.main")


class WMBot(RedBase):

    async def pre_flight(self, cli_flags):
        await super().pre_flight(cli_flags)
        self.add_cog(WestMarchesCog(self))
        await permissions(self)


def main():
    # token = os.environ.get("DISCORD_BOT_SECRET")
    # keep_alive()
    # bot = DiscordBot(ReplitDBStore(), '!')
    # bot.run(token)

    bot = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        cli_flags = Namespace(
            token=os.environ.get("DISCORD_BOT_SECRET"),
            prefix='!',
            mentionable=True,
            owner=None,
            co_owner=[],
            load_cogs=[],
            logging_level=logging.INFO,
            rpc=False,
            rpc_port=6133,
            message_cache_size=1000,
            no_message_cache=False,
            use_team_features=False,
            dry_run=False,
            dev=False,
            rich_logging=False,
            disable_intent=[],
            no_prompt=True,
            no_cogs=True)

        data_manager.basic_config = {
            'DATA_PATH': os.environ['DISCORD_BOT_DATA_PATH'],
            'COG_PATH_APPEND': 'cogs',
            'CORE_PATH_APPEND': 'core',
            'STORAGE_TYPE': 'JSON',
            'STORAGE_DETAILS': {}
        }

        bot = WMBot(
            cli_flags=cli_flags,
            description="Red V3",
            dm_help=None
        )

        exc_handler = functools.partial(global_exception_handler, bot)
        loop.set_exception_handler(exc_handler)
        fut = loop.create_task(run_bot(bot, cli_flags))
        r_exc_handler = functools.partial(red_exception_handler, bot)
        fut.add_done_callback(r_exc_handler)
        loop.run_forever()
    except SystemExit as exc:
        log.info("Shutting down with exit code: %s", exc.code)
        if bot is not None:
            loop.run_until_complete(shutdown_handler(bot, None, exc.code))
    except Exception as exc:  # Non standard case.
        log.exception("Unexpected exception (%s): ", type(exc), exc_info=exc)
        if bot is not None:
            loop.run_until_complete(shutdown_handler(bot, None, ExitCodes.CRITICAL))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        log.info("Please wait, cleaning up a bit more")
        loop.run_until_complete(asyncio.sleep(2))
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()
        exit_code = bot._shutdown_mode if bot is not None else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
