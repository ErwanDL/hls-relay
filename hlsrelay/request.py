from aiohttp import web


class RequestClient:
    def __init__(self, app: web.Application) -> None:
        self._app = app

    async def get_request(self, url: str) -> web.Response:
        async with self._app["session"].get(url) as res:
            body = await res.read()
            return web.Response(status=res.status, headers=res.headers, body=body)
