from quart import request, abort, make_response

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/')
@app.auth.required
async def index(user):
    return "Hello, {}!".format(user)

from dataclasses import dataclass

@dataclass
class ServerSentEvent:
    data: str
    retry: int | None
    event: str | None = None
    id: int | None = None

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\r\n\r\n"
        return message.encode('utf-8')

@app.get("/sse")
async def sse():
    if "text/event-stream" not in request.accept_mimetypes:
        abort(400)

    async def send_events():
        while True:
            data = (await app.tasks.pop()).id
            event = ServerSentEvent(data, 600)
            yield event.encode()

    response = await make_response(
        send_events(),
        {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        },
    )
    response.timeout = None
    return response
