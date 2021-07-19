from quart import request

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/intent/predict', methods=['POST'])
async def intent_predict():
    await app.intents.ready

    json_request = await request.json
    return {'prediction': app.intents.predict(json_request['message'])}


@app.route('/intent/<intent>/pattern')
async def intent_pattern_list(intent):
    return {'patterns': app.intents.list_patterns(intent)}


@app.route('/intent/<intent>/pattern', methods=['POST'])
@app.auth.required
async def intent_pattern_add(user, intent):
    json_request = await request.json

    app.intents.add_pattern(intent, json_request['pattern'])
    return 'Done', 204


@app.route('/intent/train', methods=['POST'])
@app.auth.required
async def intent_train(user):
    await app.intents.ready

    app.intents.train()
    return 'Done', 204

