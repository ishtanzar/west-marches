from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/')
@app.auth.required
async def index(user):
    return "Hello, {}!".format(user)
