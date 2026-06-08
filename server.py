#!/usr/bin/env python3
"""
Static file server + POST /log endpoint.
Replaces: python3 -m http.server 8010
Usage:    python3 server.py [port]
"""
import http.server
import json
import os
import sys
from datetime import datetime, timezone

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8010
LOG_FILE = os.path.join(os.path.dirname(__file__), "user_log.json")


def append_log(entry: dict):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log = []
    else:
        log = []
    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


class Handler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/log":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body)
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()
            payload["ip"] = self.client_address[0]
            append_log(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            self.send_response(500)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        # suppress per-request noise; only print errors
        if args and str(args[1]) not in ("200", "204"):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}  —  logging to {LOG_FILE}")
        httpd.serve_forever()
