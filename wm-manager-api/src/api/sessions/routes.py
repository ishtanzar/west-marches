import datetime

import dateparser
import discord
from quart import request

from api import WestMarchesApi
from services.database import SessionScheduleDocument

app = WestMarchesApi.instance


@app.route('/session', methods=['POST'])
@app.auth.required
async def chatbot_parse_session_schedule(user):
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
        # discord_msg: discord.Message = await app.discord.fetch_message(message_in['channel_id'],
        #                                                                message_in['message_id'])
        message = {'channel_id': message_in['channel_id'], 'message_id': message_in['message_id']}
        # TODO: should not read from discord
        # organizer_id = discord_msg.author.id
        # organizer = discord_msg.author.name

    else:
        # TODO: Create message
        pass

    session = SessionScheduleDocument(date, organizer_id, message)
    session.journal_id = await app.kanka.create_journal('TODO - ' + organizer, 'Rapport', date)
    session.insert()

    return session.asdict(), 201
    # session_date, announce = flask.agenda.parse_session_announce(request.json['message'])
    # flask.agenda.schedule(session_date, request.json['user_id'], request.json['message_id'])


@app.route('/session/<session_id>/characters', methods=['PATCH'])
@app.auth.required
async def set_session_players(user, session_id):
    session = SessionScheduleDocument.find_one({'_id': session_id})
    json_request = await request.json
    tags = json_request['characters']

    if session:
        await app.kanka.set_journal_tags(session.journal_id, tags)

    return session.asdict(), 201

