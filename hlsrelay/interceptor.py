import time
from enum import Enum, auto
from typing import Awaitable, Callable, Optional, TextIO, Tuple, cast
from urllib.parse import urljoin

import m3u8
from aiohttp import web


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
        full_path = urljoin(self._base_url, resource_URI)
        media_type = MediaType.from_URI(resource_URI)

        self._detect_track_switch(media_type, full_path)

        self._log(f"[IN][{media_type.name}] {full_path}")
        stream_res, time_elapsed_ms = await self._request_stream(full_path)
        self._log(f"[OUT][{media_type.name}] {full_path} ({time_elapsed_ms}ms)")

        self._save_if_is_master_playlist(media_type, cast(bytes, stream_res.body), full_path)

        return stream_res

    def _detect_track_switch(self, req_media_type: MediaType, req_full_path: str) -> None:
        if self._current_master_playlist is None or req_media_type != MediaType.MANIFEST:
            return

        if any(
            (req_full_path == playlist.absolute_uri)
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

    def _save_if_is_master_playlist(
        self, req_media_type: MediaType, res_body: bytes, req_full_path
    ) -> None:
        if req_media_type == MediaType.MANIFEST:
            playlist = m3u8.loads(res_body.decode("utf-8"))
            if playlist.is_variant:
                playlist.base_uri = urljoin(req_full_path, ".")
                self._current_master_playlist = playlist
