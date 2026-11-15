#!/usr/bin/env python3
"""Serve the repository root for the optional browser viewer.

The viewer is a static HTML page. It needs an HTTP origin because the engine
loads STEP files with XHR; opening `viewer/index.html` directly from the file
system will not work.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ViewerRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Static handler with caching disabled so model changes appear immediately."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the Dark Agent Cad repository for the optional viewer."
    )
    parser.add_argument("--port", type=int, default=8000, help="TCP port (default: 8000)")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the viewer URL in the default browser.",
    )
    args = parser.parse_args()

    handler = functools.partial(ViewerRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        url = f"http://127.0.0.1:{args.port}/viewer/"
        print(f"Serving {ROOT}")
        print(f"Open {url}")
        print("Press Ctrl+C to stop.")
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
