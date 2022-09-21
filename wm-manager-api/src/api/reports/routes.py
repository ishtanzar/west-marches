import datetime
import json
import sys

from quart import request

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/report/discord', methods=['POST'])
# @app.auth.required
async def report_from_discord():
    json_request = await request.json
    json.dump(json_request, sys.stdout, indent=2)

    journal = await app.kanka.create_journal(
        'Rapport de %s' % json_request['author']['name'],
        json_request['content'],
        'Rapport Joueur',
        datetime.datetime.fromtimestamp(json_request['created_at']))

    await app.kanka.set_entity_attribute(journal['entity_id'], '_discord_message', str(json_request['id']), private=True)
    await app.kanka.set_entity_attribute(journal['entity_id'], '_discord_author', str(json_request['author']['id']), private=True)

    return "OK", 200


@app.route('/report/discord/<message_id>', methods=['GET'])
async def find_from_discord(message_id):
    journals = await app.kanka.find_journal(attribute_name='_discord_message', attribute_value=message_id)
    return json.dumps({'reports': journals}), 200
