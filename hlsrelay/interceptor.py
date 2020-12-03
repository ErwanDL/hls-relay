import time
from enum import Enum, auto
from typing import Awaitable, Callable, Optional, TextIO
from urllib.parse import urljoin

from aiohttp import web


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
        self._last_request_type: Optional[MediaType] = None

    async def intercept(self, request: web.Request) -> web.Response:
        resource_URI = request.match_info.get("resource_URI", "")
        full_path = urljoin(self._base_url, resource_URI)
        media_type = MediaType.from_URI(resource_URI)

        if self._last_request_type == MediaType.SEGMENT and media_type == MediaType.MANIFEST:
            self._log("[TRACK SWITCH]")

        self._log(f"[IN][{media_type.name}] {full_path}")
        t1 = time.time()
        stream_res = await self._request_executor(full_path)
        t2 = time.time()
        time_elapsed_ms = round((t2 - t1) * 1000, 2)
        self._log(f"[OUT][{media_type.name}] {full_path} ({time_elapsed_ms}ms)")

        self._last_request_type = media_type
        return stream_res

    def _log(self, text: str) -> None:
        print(text, file=self._output)


class MediaType(Enum):
    MANIFEST = auto()
    SEGMENT = auto()

    @classmethod
    def from_URI(cls, resource_URI: str) -> "MediaType":
        return cls.MANIFEST if resource_URI.endswith((".m3u8", "m3u")) else cls.SEGMENT
