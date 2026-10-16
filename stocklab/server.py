"""Local-only demo server. Exact static route allowlist; no arbitrary file serving."""

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit

from .experiment import run
from .ledger import recent, save
from .model import Scenario

WEB = Path(__file__).parent / "web"
ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css"), "/example.json": ("example.json", "application/json")}
RUN_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data, content_type="application/json"):
        body = json.dumps(data, allow_nan=False).encode() if content_type == "application/json" else data
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/api/health":
            return self.reply(200, {"status": "ok", "mode": "local-demo"})
        if route == "/api/defaults":
            return self.reply(200, asdict(Scenario()))
        if route == "/api/history":
            return self.reply(200, recent(self.server.ledger_path))
        if route not in ASSETS:
            return self.reply(404, {"error": "Not found"})
        filename, content_type = ASSETS[route]
        path = WEB / filename
        if not path.exists():
            return self.reply(404, {"error": "Asset not found"})
        if content_type == "application/json":
            return self.reply(200, json.loads(path.read_text()))
        self.reply(200, path.read_bytes(), content_type)

    def do_POST(self):
        if self.path != "/api/run":
            return self.reply(404, {"error": "Not found"})
        # Reject cross-origin requests to this unauthenticated local demo.
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.reply(403, {"error": "Cross-origin requests are not allowed"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "Use application/json"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 16_384:
                return self.reply(413, {"error": "Request body must be between 1 and 16384 bytes"})
            self.connection.settimeout(10)
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("request must be a JSON object")
            if set(payload) - {"scenario", "n", "replicates", "seed", "method"}:
                raise ValueError("unknown request field")
            scenario = Scenario(**payload.pop("scenario", {}))
            if not RUN_LOCK.acquire(blocking=False):
                return self.reply(429, {"error": "A simulation is already running; try again shortly"})
            try:
                result = run(scenario, **payload)
                result["ledger_id"] = save(result, self.server.ledger_path)
            finally:
                RUN_LOCK.release()
            self.reply(200, result)
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            self.reply(400, {"error": str(exc)})
        except (OSError, TimeoutError):
            self.reply(500, {"error": "Local I/O failure; inspect server output"})

    def log_message(self, fmt, *args):
        # No bodies, cookies, credentials, or arbitrary paths in logs.
        print(f"StockSense HTTP {args[1] if len(args) > 1 else 'request'}", flush=True)


def create_server(host="127.0.0.1", port=8000, ledger_path="output/experiments.db"):
    server = ThreadingHTTPServer((host, port), Handler)
    server.ledger_path = ledger_path
    return server


def serve(host="127.0.0.1", port=8000):
    server = create_server(host, port)
    print(f"StockSense local demo: http://{host}:{server.server_port}", flush=True)
    print("Development server only; use a production gateway, authentication and quotas for public hosting.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
