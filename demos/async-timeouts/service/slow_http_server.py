"""Serve the URI demo's slow response in OpenShift or a local test process."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import threading
import time


class Handler(BaseHTTPRequestHandler):
    """Handle the delayed demo request and immediate health checks."""

    def do_GET(self) -> None:
        """Delay the response long enough to demonstrate a socket timeout."""
        if self.path == "/healthz":
            body = json.dumps({"status": "ok"}).encode()
        elif self.path == "/slow":
            time.sleep(3)
            body = json.dumps({"message": "Delayed response completed"}).encode()
        else:
            self.send_error(404)
            return
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The first request deliberately disconnects before we respond.
            pass

    def log_message(self, _format: str, *args: object) -> None:
        """Keep fixture access logs out of the teaching output."""


def main() -> None:
    """Listen until terminated; optionally publish a local test endpoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--state-directory", type=Path)
    args = parser.parse_args()
    with ThreadingHTTPServer((args.bind, args.port), Handler) as server:
        server.daemon_threads = True

        def stop_server(_signum: int, _frame: object) -> None:
            # shutdown must run outside the thread executing serve_forever.
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGTERM, stop_server)
        signal.signal(signal.SIGINT, stop_server)
        if args.state_directory:
            state = {
                "url": f"http://127.0.0.1:{server.server_port}",
                "pid": os.getpid(),
            }
            state_file = args.state_directory / "endpoint.json"
            temporary = state_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(state), encoding="utf-8")
            temporary.replace(state_file)
        server.serve_forever(poll_interval=0.1)


if __name__ == "__main__":
    main()
