# HLS Relay Server

This project is a Python server capable of intercepting, logging and forwarding requests made to an HLS stream through a media player (ex: VLC).

## Installation

This project was developed and tested with Python >= 3.8

-   Create a virtual environment for this project :

    ```
    $ python -m venv <venv-name>
    ```

-   Activate your virtual environment, and install the required dependencies :
    ```
    $ pip install -r requirements.txt
    ```

The project uses [black](https://github.com/psf/black) as a formatter, and [flake8](https://flake8.pycqa.org/en/latest/) as a linter.

## Running tests

This project is tested with the [unittest](https://docs.python.org/3/library/unittest.html) framework, included in the standard library.

You can run the tests by navigating to the project root and running :

```
$ python -m unittest -v
```

Be aware that the integration tests (under `test/integration/`) require an internet connection to function properly.

## Running the server

You can run the server by navigating to the project root and running :

```
$ python -m hlsrelay <base-url>
```

For example:

```
$ python -m hlsrelay https://bitdash-a.akamaihd.net
```

You can then start VLC, click on "File > Open Network...", and then request http://localhost:8080/\<stream-file-uri\>. For example, entering http://localhost:8080/content/sintel/hls/playlist.m3u8 will request the m3u8 file at https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8.

## Project structure

The source code is located under `hlsrelay/` :

-   `__main__.py` is the entry point of the app, it parses command line args and boots up the server.
-   `server.py` defines a `create_app` function for initializing an [aiohttp](https://docs.aiohttp.org/en/stable/) server, given a base URL to the stream to intercept, and an optional output stream.
-   `interceptor.py` contains the main logic of the interceptor : logging and forwarding requests, detecting track switches and handling both relative and absolute URLs in m3u8 manifests.
-   `request.py` is a simple wrapper to perform HTTP requests while reusing the same persistent `aiohttp.ClientSession`.
-   `config.py` contains basic server configuration variables.

The test code is located under `test/` :

-   Unit tests for the interceptor are located in `test/unit/`.
-   Integration tests, running a full-fledged server, are located in `test/integration/`. As these tests perform real HTTP requests to actual stream URLs, you need to have an internet connection to run them.

## Additional comments on the methodology

-   To detect track switches (bitrate changes in the case of an adaptive bitrate stream), we chose to save the current master playlist (we use [the Python m3u8 library](https://github.com/globocom/m3u8) to parse playlist files and detect adaptive bitrates) as an attribute of the `StreamInterceptor`. Then, if another playlist file is requested, and it was listed as a sub-playlist of the current master playlist, we log a track switch.
-   To be able to handle both absolute and relative URLs, we simply look for absolute URLs in playlist files (lines starting with `http://` or `https://`), and replace the base URL with that of our server (`http://localhost:8080`).
