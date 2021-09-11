from compose.project import NoSuchService

from api import WestMarchesApi
from quart import request

app = WestMarchesApi.instance


@app.route('/foundry/restart', methods=['POST'])
@app.auth.required
async def restart(user):
    try:
        app.compose.restart('foundry')
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@app.route('/foundry/actors')
async def foundry_actors():
    return app.foundryvtt.find_actors()


@app.route('/foundry/users', methods=['POST'])
@app.auth.required
async def foundry_users_add(user):
    json_request = await request.json
    name = json_request['name']
    discord = json_request['discord']

    user_id = app.foundryvtt.add_user(name, discord)

    return {
        'user_id': user_id
    }


@app.route('/foundry/users/<user_id>', methods=['PUT'])
async def foundry_users_update(user, user_id):
    json_request = await request.json

    name = json_request['name'] if 'name' in json_request else None
    role = json_request['role'] if 'role' in json_request else None

    app.foundryvtt.update_user(user_id, name, role)

    return 'Done', 204
