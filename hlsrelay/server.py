from aiohttp import web


async def handle(request: web.Request) -> web.Response:
    print(request.match_info)
    return web.Response()


def create_app() -> web.Application:
    app = web.Application()
    app.add_routes([web.get("/", handle), web.get("/{name}", handle)])
    return app
