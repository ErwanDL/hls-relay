from io import StringIO
from unittest import IsolatedAsyncioTestCase, mock

from aiohttp import web
from hlsrelay.interceptor import StreamInterceptor

test_headers = {
    "Accept-Ranges": "bytes",
    "Content-Type": "audio/x-mpegurl",
    "Etag": '"a852221858992283a46628accca46f33:1509454736"',
    "Last-Modified": "Tue, 31 Oct 2017 12:58:56 GMT",
    "Server": "TestServer",
    "Content-Length": "9",
    "Expires": "Tue, 01 Dec 2020 10:00:34 GMT",
    "Cache-Control": "max-age=0, no-cache, no-store",
    "Pragma": "no-cache",
    "Date": "Tue, 01 Dec 2020 10:00:34 GMT",
    "Connection": "keep-alive",
    "Access-Control-Max-Age": "86400",
    "Access-Control-Allow-Credentials": "false",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET,POST,HEAD",
    "Access-Control-Allow-Origin": "*",
}


async def fake_request_executor(url: str) -> web.Response:
    return web.Response(
        status=206,
        body=bytes(f"A test request was sent to {url}", encoding="utf-8"),
        headers=test_headers,
    )


class TestStreamInterceptorBasic(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.output = StringIO()
        self.interceptor = StreamInterceptor(
            "http://test.com", request_executor=fake_request_executor, output=self.output
        )

    async def test_relays_correct_response(self) -> None:
        mock_request = mock.MagicMock(match_info={"resource_URI": "playlist.m3u8"})
        res = await self.interceptor.intercept(mock_request)
        self.assertEqual(res.status, 206)
        self.assertEqual(res.headers, test_headers)
        self.assertEqual(res.body, b"A test request was sent to http://test.com/playlist.m3u8")

    async def test_logs_with_playlist_file(self) -> None:
        mock_request = mock.MagicMock(match_info={"resource_URI": "playlist.m3u8"})
        _ = await self.interceptor.intercept(mock_request)

        logs = self.output.getvalue().splitlines()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], "[IN][MANIFEST] http://test.com/playlist.m3u8")
        self.assertRegex(
            logs[1], r"\[OUT\]\[MANIFEST\] http://test.com/playlist.m3u8 \([0-9]+\.[0-9]+ms\)"
        )

    async def test_logs_with_segment_file(self) -> None:
        mock_request = mock.MagicMock(match_info={"resource_URI": "video.ts"})
        _ = await self.interceptor.intercept(mock_request)

        logs = self.output.getvalue().splitlines()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], "[IN][SEGMENT] http://test.com/video.ts")
        self.assertRegex(
            logs[1], r"\[OUT\]\[SEGMENT\] http://test.com/video.ts \([0-9]+\.[0-9]+ms\)"
        )


async def track_switch_test_request_executor(url: str) -> web.Response:
    if url.endswith("manifest.m3u8"):
        return web.Response(
            status=200,
            body=b"""#EXTM3U
#EXT-X-VERSION:5

#EXT-X-STREAM-INF:BANDWIDTH=628000,CODECS="avc1.42c00d,mp4a.40.2",RESOLUTION=320x180
video_180.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=928000,CODECS="avc1.42c00d,mp4a.40.2",RESOLUTION=480x270
video_270.m3u8""",
        )
    else:
        return web.Response(status=200, body=b"Test body")


class TestStreamInterceptorTrackSwitch(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.output = StringIO()
        self.interceptor = StreamInterceptor(
            "http://test.com",
            request_executor=track_switch_test_request_executor,
            output=self.output,
        )

    async def test_detects_track_switch(self) -> None:
        mock_request_master_playlist = mock.MagicMock(match_info={"resource_URI": "manifest.m3u8"})
        _ = await self.interceptor.intercept(mock_request_master_playlist)

        mock_request_video_180 = mock.MagicMock(match_info={"resource_URI": "video_180.m3u8"})
        _ = await self.interceptor.intercept(mock_request_video_180)

        mock_request_video_270 = mock.MagicMock(match_info={"resource_URI": "video_270.m3u8"})
        _ = await self.interceptor.intercept(mock_request_video_270)

        logs = self.output.getvalue().splitlines()
        self.assertEqual(logs[-3], "[TRACK SWITCH]")
        self.assertEqual(logs.count("[TRACK SWITCH]"), 1)

    async def test_no_track_switch_if_not_in_manifest(self) -> None:
        mock_request_master_playlist = mock.MagicMock(match_info={"resource_URI": "manifest.m3u8"})
        _ = await self.interceptor.intercept(mock_request_master_playlist)

        mock_request_video_180 = mock.MagicMock(match_info={"resource_URI": "video_180.m3u8"})
        _ = await self.interceptor.intercept(mock_request_video_180)

        mock_request_other_video = mock.MagicMock(match_info={"resource_URI": "other_video.m3u8"})
        _ = await self.interceptor.intercept(mock_request_other_video)

        logs = self.output.getvalue().splitlines()
        self.assertNotIn("[TRACK SWITCH]", logs)
