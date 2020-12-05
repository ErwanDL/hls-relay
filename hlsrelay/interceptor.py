import time
from enum import Enum, auto
from typing import Awaitable, Callable, Optional, TextIO, Tuple, cast
from urllib.parse import urljoin, urlparse

import m3u8
from aiohttp import web

from hlsrelay.config import HOST, PORT


class MediaType(Enum):
    MANIFEST = auto()
    SEGMENT = auto()

    @classmethod
    def from_URI(cls, resource_URI: str) -> "MediaType":
        return cls.MANIFEST if resource_URI.endswith((".m3u8", "m3u")) else cls.SEGMENT


class StreamInterceptor:
    def __init__(
        self,
        base_url: str,
        request_executor: Callable[[str], Awaitable[web.Response]],
        output: TextIO,
    ) -> None:
        self._base_url = base_url
        self._request_executor = request_executor
        self._output = output
        self._current_master_playlist: Optional[m3u8.M3U8] = None
        self._first_track_started = False

    async def intercept(self, request: web.Request) -> web.Response:
        resource_URI = request.match_info.get("resource_URI", "")
        full_url = urljoin(self._base_url, resource_URI)
        media_type = MediaType.from_URI(resource_URI)

        if media_type == MediaType.MANIFEST:
            self._detect_track_switch(full_url)

        self._log(f"[IN][{media_type.name}] {full_url}")
        stream_res, time_elapsed_ms = await self._request_stream(full_url)
        self._log(f"[OUT][{media_type.name}] {full_url} ({time_elapsed_ms}ms)")

        if media_type == MediaType.MANIFEST:
            stream_res_body_str = cast(bytes, stream_res.body).decode("utf-8")
            self._save_if_is_master_playlist(stream_res_body_str, full_url)
            interceptor_res_body = self._handle_absolute_urls(stream_res_body_str)
        else:
            interceptor_res_body = stream_res.body

        return web.Response(status=200, body=interceptor_res_body)

    def _detect_track_switch(self, req_full_url: str) -> None:
        if self._current_master_playlist is None:
            return

        if any(
            (req_full_url == playlist.absolute_uri)
            for playlist in self._current_master_playlist.playlists
        ):
            if not self._first_track_started:
                self._first_track_started = True
            else:
                self._log("[TRACK SWITCH]")

    def _log(self, text: str) -> None:
        print(text, file=self._output)

    async def _request_stream(self, path: str) -> Tuple[web.Response, float]:
        t1 = time.time()
        stream_res = await self._request_executor(path)
        t2 = time.time()
        time_elapsed_ms = round((t2 - t1) * 1000, 2)

        return stream_res, time_elapsed_ms

    def _save_if_is_master_playlist(self, res_body: str, req_full_url: str) -> None:
        playlist = m3u8.loads(res_body)
        if playlist.is_variant:
            playlist.base_uri = urljoin(req_full_url, ".")
            self._current_master_playlist = playlist

    @staticmethod
    def _handle_absolute_urls(res_body: str) -> bytes:
        """If absolute URLs are detected in the manifest, we replace the host name
        with that of our local server."""
        adjusted_body_lines = []

        for line in res_body.split("\n"):
            if line.startswith(("http://", "https://")):
                parse_result = urlparse(line)
                adjusted_body_lines.append(f"http://{HOST}:{PORT}" + parse_result.path)
            else:
                adjusted_body_lines.append(line)

        return bytes("\n".join(adjusted_body_lines), encoding="utf-8")
