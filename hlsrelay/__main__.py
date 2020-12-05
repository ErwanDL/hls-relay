from argparse import ArgumentParser

from aiohttp import web

from hlsrelay.config import HOST, PORT
from hlsrelay.server import create_app

if __name__ == "__main__":
    parser = ArgumentParser(description="HLS relay server")
    parser.add_argument("base_url", type=str, nargs=1, help="Base URL of the stream to relay")

    args = parser.parse_args()
    base_url = args.base_url[0]

    app = create_app(base_url)
    web.run_app(app, host=HOST, port=PORT)
