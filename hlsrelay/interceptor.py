import time
from typing import Awaitable, Callable, TextIO
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

    async def intercept(self, request: web.Request) -> web.Response:
        path_to_resource = request.match_info.get("path_to_resource", "")
        full_path = urljoin(self._base_url, path_to_resource)
        self._log(f"[IN] {full_path}")
        t1 = time.time()
        stream_res = await self._request_executor(full_path)
        t2 = time.time()
        time_elapsed_ms = round(t2 - t1, 6) * 1000
        self._log(f"[OUT] {full_path} ({time_elapsed_ms}ms)")
        return stream_res

    def _log(self, text: str) -> None:
        print(text, file=self._output)
