from aiohttp import web

TEST_HEADERS = {
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


async def dummy_request_executor(_: str) -> web.Response:
    return web.Response(status=200, body=b"Test body", headers=TEST_HEADERS)


async def content_test_request_executor(url: str) -> web.Response:
    if url == "http://test.com/manifest-absolute.m3u8":
        body = b"""#EXTM3U
#EXT-X-VERSION:3
#EXTINF:2.0,
http://test.com/media-1.ts
#EXTINF:2.0,
https://test.com/media-1.ts
"""
    elif url == "http://test.com/manifest-relative.m3u8":
        body = b"""#EXTM3U
#EXT-X-VERSION:3
#EXTINF:2.0,
media-1.ts
#EXTINF:2.0,
media-1.ts
"""
    else:
        body = b"\xb4\xb1\x03\xc3\xa2\x12"

    return web.Response(status=200, body=body, headers=TEST_HEADERS)


async def track_switch_test_request_executor(url: str) -> web.Response:
    if url == "http://test.com/manifest.m3u8":
        body = b"""#EXTM3U
#EXT-X-VERSION:5

#EXT-X-STREAM-INF:BANDWIDTH=628000,CODECS="avc1.42c00d,mp4a.40.2",RESOLUTION=320x180
video_180.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=928000,CODECS="avc1.42c00d,mp4a.40.2",RESOLUTION=480x270
video_270.m3u8
"""
    else:
        body = b"Test Body"

    return web.Response(status=200, body=body, headers=TEST_HEADERS)
