import datetime
from typing import Optional

import dateparser
import discord
from compose.project import NoSuchService
from quart import request

from api import WestMarchesApi
from services.database import SessionScheduleDocument
from services.kanka import KankaService

app = WestMarchesApi.instance


@app.route('/')
@app.auth.required
async def index(user):
    return "Hello, {}!".format(user)


@app.route('/container/restart/<service_name>', methods=['POST'])
@app.auth.required
async def restart_container(service_name, user):
    try:
        app.compose.restart(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@app.route('/backup/list')
@app.auth.required
async def backup_list(user):
    return {
        'backups': [backup.asdict(serializable=True) for backup in app.backup.list(sort=[('date', 1)])]
    }


@app.route('/backup/perform', methods=['POST'])
@app.auth.required
async def backup_perform(user):
    service_name = 'foundry'
    error: Optional[Exception] = None

    try:
        app.compose.stop(service_name)

        try:
            for schema in ['worlds', 'systems', 'modules']:
                app.backup.perform(schema)
        except Exception as nse:
            error = nse

        app.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as nse:
        return str(nse), 500


@app.route('/backup/restore/<backup_id>', methods=['POST'])
@app.auth.required
async def backup_restore(user, backup_id):
    service_name = 'foundry'
    error: Optional[Exception] = None

    try:
        app.compose.stop(service_name)

        try:
            app.backup.restore(backup_id)
        except Exception as ex:
            error = ex

        app.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as ex:
        return str(ex), 500


@app.route('/session', methods=['POST'])
async def chatbot_parse_session_schedule():
    """
    {
        "date": "",
        "organizer: "<USER_ID>"
        "message": {
            "channel_id": "<DISCORD_CHANNEL_ID>",
            "message_id": "<DISCORD_MESSAGE_ID>",
        },
    }
    """
    message: dict = {}
    date: datetime.datetime
    organizer_id: int
    organizer: str

    json_request = await request.json
    message_in = json_request['message']
    date_in = json_request['date']
    organizer_id = json_request['organizer'] if 'organizer' in json_request else None
    organizer = ''

    date = dateparser.parse(date_in, locales=["fr"], settings={'PREFER_DATES_FROM': 'future'})

    if type(message_in) is dict:
        discord_msg: discord.Message = await app.discord.fetch_message(message_in['channel_id'],
                                                                       message_in['message_id'])
        message = {'channel_id': message_in['channel_id'], 'message_id': message_in['message_id']}
        organizer_id = discord_msg.author.id
        organizer = discord_msg.author.name

    else:
        # TODO: Create message
        pass

    session = SessionScheduleDocument(date, organizer_id, message)
    session.journal_id = await app.kanka.create_journal('TODO - ' + organizer, 'Rapport', date)
    session.insert()

    return session.asdict(), 201
    # session_date, announce = flask.agenda.parse_session_announce(request.json['message'])
    # flask.agenda.schedule(session_date, request.json['user_id'], request.json['message_id'])


@app.route('/roster')
async def foundry_roster():
    return {
        'heroes': app.foundryvtt.find_actors()
    }
