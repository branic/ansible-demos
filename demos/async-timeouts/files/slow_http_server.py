"""Serve a delayed HTTP response on an ephemeral loopback port for the URI demo."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time


class Handler(BaseHTTPRequestHandler):
    """Handle the demo request and a graceful shutdown request."""

    def do_GET(self) -> None:
        """Delay the response long enough to demonstrate a socket timeout."""
        if self.path != "/slow":
            self.send_error(404)
            return
        time.sleep(3)
        body = json.dumps({"message": "Delayed response completed"}).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The first request deliberately disconnects before we respond.
            pass

    def do_POST(self) -> None:
        """Stop only this fixture's server, after responding to the caller."""
        if self.path != "/shutdown":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format: str, *args: object) -> None:
        """Keep fixture access logs out of the teaching output."""


def main() -> None:
    """Publish readiness only after binding the listening socket."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-directory", type=Path, required=True)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        state = {"url": f"http://127.0.0.1:{server.server_port}", "pid": os.getpid()}
        state_file = args.state_directory / "endpoint.json"
        temporary = state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(state), encoding="utf-8")
        temporary.replace(state_file)
        server.serve_forever(poll_interval=0.1)


if __name__ == "__main__":
    main()
