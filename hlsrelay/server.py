import sys
from typing import TextIO

from aiohttp import web

from hlsrelay.interceptor import StreamInterceptor
from hlsrelay.request import get_request


def create_app(base_url: str, out: TextIO = sys.stdout) -> web.Application:
    app = web.Application()
    interceptor = StreamInterceptor(base_url, request_executor=get_request, output=out)
    app.add_routes([web.get("/{path_to_resource:.*}", interceptor.intercept)])
    return app
