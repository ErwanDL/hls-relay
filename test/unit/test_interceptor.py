from io import StringIO
from test.unit.utils import (
    content_test_request_executor,
    dummy_request_executor,
    track_switch_test_request_executor,
)
from unittest import IsolatedAsyncioTestCase, mock

from hlsrelay.interceptor import StreamInterceptor


class TestStreamInterceptorLogging(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.output = StringIO()
        self.interceptor = StreamInterceptor(
            "http://test.com", request_executor=dummy_request_executor, output=self.output
        )

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


class TestStreamInterceptorResponse(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.output = StringIO()
        self.interceptor = StreamInterceptor(
            "http://test.com", request_executor=content_test_request_executor, output=self.output
        )

    async def test_forwards_segment_response_without_modification(self) -> None:
        mock_request_segment = mock.MagicMock(match_info={"resource_URI": "segment.ts"})
        res = await self.interceptor.intercept(mock_request_segment)

        self.assertEqual(res.body, b"\xb4\xb1\x03\xc3\xa2\x12")

    async def test_forwards_relative_manifest_without_modification(self) -> None:
        mock_request_relative_manifest = mock.MagicMock(
            match_info={"resource_URI": "manifest-relative.m3u8"}
        )
        res = await self.interceptor.intercept(mock_request_relative_manifest)

        self.assertEqual(
            res.body,
            b"""#EXTM3U
#EXT-X-VERSION:3
#EXTINF:2.0,
media-1.ts
#EXTINF:2.0,
media-1.ts
""",
        )

    async def test_forwards_absolute_manifest_with_modified_host(self) -> None:
        mock_request_relative_manifest = mock.MagicMock(
            match_info={"resource_URI": "manifest-absolute.m3u8"}
        )
        res = await self.interceptor.intercept(mock_request_relative_manifest)

        self.assertEqual(
            res.body,
            b"""#EXTM3U
#EXT-X-VERSION:3
#EXTINF:2.0,
http://localhost:8080/media-1.ts
#EXTINF:2.0,
http://localhost:8080/media-1.ts
""",
        )


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
