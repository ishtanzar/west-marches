from dataclasses import asdict

from quart import jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden

from api import WestMarchesApi
from services.discord import DiscordError
from services.scaleway import ScalewayError


app = WestMarchesApi.instance
_MEMBER_FIELDS = ("type", "discord_username", "discord_id")


@app.after_request
async def no_store(response):
    if request.path.startswith("/s3/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


async def member_body():
    data = await request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != set(_MEMBER_FIELDS):
        raise BadRequest("Expected type, discord_username and discord_id.")
    if data["type"] != "discord":
        raise BadRequest("Member type must be discord.")
    try:
        return app.discord.validate_member(data["discord_id"], data["discord_username"])
    except DiscordError as error:
        error.to_http_error()


@app.post("/s3/credentials")
@app.auth.required
async def credentials():
    username, member_id = await member_body()
    try:
        current_username = await app.discord.member(member_id)
    except DiscordError as error:
        error.to_http_error()
    if username != current_username:
        raise Forbidden("Discord username does not match the member.")
    try:
        result = await app.scaleway.credentials(member_id, username)
    except ScalewayError as error:
        error.to_http_error()
    return jsonify(asdict(result))


@app.post("/s3/credential/revoke")
@app.auth.required
async def revoke():
    username, member_id = await member_body()
    try:
        return jsonify(await app.scaleway.revoke(member_id, username))
    except ScalewayError as error:
        error.to_http_error()
