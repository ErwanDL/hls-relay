import argparse

from aiohttp import web

from hlsrelay.server import create_app

a = 2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HLS relay server")
    parser.add_argument("stream_url", type=str, nargs=1, help="URL to the stream to relay")

    args = parser.parse_args()
    stream_url = args.stream_url[0]

    app = create_app()
    web.run_app(app, host="localhost", port=8000)
