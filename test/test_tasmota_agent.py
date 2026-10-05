import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


AGENT = (
    Path(__file__).resolve().parents[1]
    / "local/lib/python3/cmk_addons/plugins/tasmota/libexec/agent_tasmota"
)
LOADER = importlib.machinery.SourceFileLoader("agent_tasmota", str(AGENT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class TasmotaAgentTests(unittest.TestCase):
    def test_ipv4_status_url(self):
        self.assertEqual(
            MODULE.device_url("192.0.2.51", 80),
            "http://192.0.2.51:80/cm?cmnd=Status%200",
        )

    def test_ipv6_status_url_is_bracketed(self):
        self.assertEqual(
            MODULE.device_url("fd00::51", 80),
            "http://[fd00::51]:80/cm?cmnd=Status%200",
        )

    def test_agent_polls_status_and_sends_referer(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append((self.path, self.headers.get("Referer")))
                body = json.dumps({"StatusSTS": {"UptimeSec": 12}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--address",
                    "127.0.0.1",
                    "--port",
                    str(server.server_address[1]),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

        self.assertEqual(
            requests,
            [
                (
                    "/cm?cmnd=Status%200",
                    f"http://127.0.0.1:{server.server_address[1]}/",
                )
            ],
        )
        self.assertEqual(result.stdout.splitlines()[0], "<<<tasmota:sep(0)>>>")
        self.assertEqual(json.loads(result.stdout.splitlines()[1]), {"StatusSTS": {"UptimeSec": 12}})


if __name__ == "__main__":
    unittest.main()