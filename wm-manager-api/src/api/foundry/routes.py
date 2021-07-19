from compose.project import NoSuchService

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/foundry/restart', methods=['POST'])
@app.auth.required
async def restart(user):
    try:
        app.compose.restart('foundry')
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@app.route('/foundry/roster')
async def foundry_roster():
    return {
        'heroes': app.foundryvtt.find_actors()
    }
