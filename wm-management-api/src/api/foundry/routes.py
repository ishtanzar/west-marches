import logging

from quart import request

from api import WestMarchesApi
from services.docker import NoSuchService

app = WestMarchesApi.instance
logger = logging.getLogger('foundry')


@app.route('/foundry/restart', methods=['POST'])
@app.auth.required
async def restart(_):
    try:
        app.compose.restart('foundry')
    except NoSuchService as nse:
        logger.exception(nse)
        return nse.msg, 404

    return 'Done', 204


@app.route('/foundry/actors', methods=['SEARCH'])
async def foundry_actors():
    return await app.foundryvtt.actors.find(await request.json)


@app.route('/foundry/activity')
async def foundry_activity():
    return await app.foundryvtt.activity.get()


@app.route('/foundry/users', methods=['SEARCH'])
@app.auth.required
async def foundry_users(_):
    return await app.foundryvtt.users.find(await request.json)


@app.route('/foundry/users', methods=['POST'])
@app.auth.required
async def foundry_users_add(_):
    return await app.foundryvtt.users.create(await request.json)


@app.route('/foundry/users/<user_id>', methods=['PUT'])
@app.auth.required
async def foundry_users_update(_, user_id):
    return await app.foundryvtt.users.update(user_id, await request.json)
