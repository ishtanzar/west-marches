import time
from quart import Response, request

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.before_request
def on_request():
    WestMarchesApi.log.debug('on_request')
    request.start_time = time.time()


@app.after_request
async def on_response(response: Response) -> Response:
    WestMarchesApi.log.debug("on_response")

    msg = ""
    if response.status_code >= 400:
        msg = response.get_data(True)

    WestMarchesApi.log.info(msg, extra={
        'exec_time': time.time() - request.start_time,
        'useragent': request.user_agent,
        'http_method': request.method,
        'request_scheme': request.scheme,
        'http_status': response.status_code,
        'url': request.url,
        'content_type': response.mimetype,
        'query_string': request.query_string,
        'data': await request.data,
        'referrer': request.referrer,
    })

    return response
