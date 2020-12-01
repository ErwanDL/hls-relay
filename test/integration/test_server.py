from io import StringIO
from pathlib import Path
from typing import Tuple
from unittest import IsolatedAsyncioTestCase

from aiohttp import ClientResponse, web
from aiohttp.test_utils import TestClient, TestServer
from hlsrelay.server import create_app


class TestIntegrationServer(IsolatedAsyncioTestCase):
    async def query_relay_server(
        self, app: web.Application, resource_path: str
    ) -> Tuple[ClientResponse, bytes]:
        async with TestClient(TestServer(app)) as client:
            res = await client.get(resource_path)
            body = await res.read()
            return res, body

    async def test_bitdash_stream(self) -> None:
        out = StringIO()
        app = create_app("https://bitdash-a.akamaihd.net", out=out)
        res, body = await self.query_relay_server(
            app,
            "/content/MI201109210084_1/m3u8s/f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8",
        )
        self.assertTrue(res.ok)
        with (
            Path(__file__).parent / "test_data" / "f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8.body"
        ).open("rb") as f:
            expected_body = f.read()
            self.assertEqual(body, expected_body)
