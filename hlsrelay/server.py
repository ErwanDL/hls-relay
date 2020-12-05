import sys
from typing import TextIO

from aiohttp import web
from aiohttp.client import ClientSession

from hlsrelay.interceptor import StreamInterceptor
from hlsrelay.request import RequestClient


async def persistent_session(app: web.Application):
    app["session"] = ClientSession()
    yield
    await app["session"].close()


def create_app(base_url: str, out: TextIO = sys.stdout) -> web.Application:
    app = web.Application()
    client = RequestClient(app)
    interceptor = StreamInterceptor(base_url, request_executor=client.get_request, output=out)
    app.add_routes([web.get("/{resource_URI:.*}", interceptor.intercept)])
    app.cleanup_ctx.append(persistent_session)
    return app
