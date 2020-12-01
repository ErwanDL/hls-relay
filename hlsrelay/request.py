from aiohttp import ClientSession, web


async def get_request(url: str) -> web.Response:
    async with ClientSession() as session:
        async with session.get(url) as res:
            body = await res.read()
            return web.Response(status=res.status, headers=res.headers, body=body)
