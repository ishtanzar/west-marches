import logging

from quart import request

from api import WestMarchesApi
from services.docker import NoSuchService

app = WestMarchesApi.instance
logger = logging.getLogger('foundry')


@app.route('/foundry/restart', methods=['POST'])
@app.auth.required
async def restart(user):
    try:
        app.compose.restart('foundry')
    except NoSuchService as nse:
        logger.exception(nse)
        return nse.msg, 404

    return 'Done', 204


@app.route('/foundry/actors')
async def foundry_actors():
    return app.foundryvtt.get('/api/actors').json()


@app.route('/foundry/activity')
async def foundry_activity():
    return app.foundryvtt.get('/api/activity').json()


@app.route('/foundry/users')
@app.auth.required
async def foundry_users(user):
    return app.foundryvtt.get('/api/users', params=request.args).json()


@app.route('/foundry/users', methods=['POST'])
@app.auth.required
async def foundry_users_add(user):
    return app.foundryvtt.post('/api/users', json=await request.json).json()


@app.route('/foundry/users/<user_id>', methods=['PUT'])
@app.auth.required
async def foundry_users_update(user, user_id):
    body = await request.json
    return app.foundryvtt.put('/api/users/%s' % user_id, json=body).json()
