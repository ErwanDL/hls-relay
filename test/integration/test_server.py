import warnings
from io import StringIO
from pathlib import Path
from typing import Tuple
from unittest import IsolatedAsyncioTestCase

from aiohttp import ClientResponse
from aiohttp.test_utils import TestClient, TestServer
from hlsrelay.server import create_app


class TestIntegrationServer(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # aiohttp/asyncio emits ResourceWarning sporadically on some tests.
        # This is apparently due to the event loop closing before the session itself :
        # https://docs.aiohttp.org/en/latest/client_advanced.html#graceful-shutdown
        warnings.filterwarnings("ignore", category=ResourceWarning)

    async def test_bitdash_m3u8_1(self) -> None:
        base_url = "https://bitdash-a.akamaihd.net"
        resource_path = "/content/MI201109210084_1/m3u8s/f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8"
        exp_filename = "bitdash-f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8.body"
        await self._assert_server_relays_correct_response_and_logs(
            base_url, resource_path, exp_filename
        )

    async def test_bitdash_m3u8_2(self) -> None:
        base_url = "https://bitdash-a.akamaihd.net"
        resource_path = "/content/sintel/hls/playlist.m3u8"
        exp_filename = "bitdash-playlist.m3u8.body"
        await self._assert_server_relays_correct_response_and_logs(
            base_url, resource_path, exp_filename
        )

    async def test_mux_m3u8(self) -> None:
        base_url = "https://test-streams.mux.dev"
        resource_path = "/x36xhzz/x36xhzz.m3u8"
        exp_filename = "mux-x36xhzz.m3u8.body"
        await self._assert_server_relays_correct_response_and_logs(
            base_url, resource_path, exp_filename
        )

    async def test_bitdash_video_segment(self) -> None:
        base_url = "https://bitdash-a.akamaihd.net"
        resource_path = "/content/MI201109210084_1/video/1080_4800000/hls/segment_0.ts"
        exp_filename = "bitdash-video-segment_0.ts.body"
        await self._assert_server_relays_correct_response_and_logs(
            base_url, resource_path, exp_filename
        )

    async def test_bitdash_audio_segment(self) -> None:
        base_url = "https://bitdash-a.akamaihd.net"
        resource_path = "/content/MI201109210084_1/audio/1_stereo_128000/hls/segment_2.ts"
        exp_filename = "bitdash-audio-segment_2.ts.body"
        await self._assert_server_relays_correct_response_and_logs(
            base_url, resource_path, exp_filename
        )

    async def _assert_server_relays_correct_response_and_logs(
        self, base_url: str, resource_path: str, expected_body_filename: str
    ) -> None:
        res, body, out = await self._query_through_relay_server(
            base_url,
            resource_path,
        )
        self._assert_status_ok_and_body(res, body, expected_body_filename)
        self._assert_logs_ins_and_outs(out)

    async def _query_through_relay_server(
        self, base_url: str, resource_path: str
    ) -> Tuple[ClientResponse, bytes, StringIO]:
        out = StringIO()
        app = create_app(base_url, out)
        async with TestClient(TestServer(app)) as client:
            res = await client.get(resource_path)
            body = await res.read()
            res.close()
            return res, body, out

    def _assert_status_ok_and_body(
        self, res: ClientResponse, body: bytes, expected_body_filename: str
    ) -> None:
        self.assertTrue(res.ok)
        with (Path(__file__).parent / "test_data" / expected_body_filename).open("rb") as f:
            expected_body = f.read()
            self.assertEqual(body, expected_body)

    def _assert_logs_ins_and_outs(self, out: StringIO) -> None:
        logs = out.getvalue().splitlines()
        self.assertEqual(len(logs), 2)
        self.assertTrue(logs[0].startswith("[IN]"))
        self.assertTrue(logs[1].startswith("[OUT]"))
