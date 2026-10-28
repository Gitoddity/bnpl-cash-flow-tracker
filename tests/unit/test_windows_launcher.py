"""Exercise launcher readiness checks against a real local HTTP endpoint."""

import os
from pathlib import Path
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest


pytestmark = pytest.mark.skipif(
    os.name != "nt" or not shutil.which("powershell.exe"),
    reason="The BAT launcher uses Windows PowerShell",
)


@pytest.mark.parametrize("initial_response", ["unavailable", "html"])
def test_launcher_waits_for_proxied_api_health(initial_response):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            starting = len(requests) <= 2
            self.send_response(503 if starting and initial_response == "unavailable" else 200)
            self.send_header("Content-Type", "text/html" if starting else "application/json")
            self.end_headers()
            self.wfile.write(b"<html>Starting</html>" if starting else b'{"status":"ok"}')

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = Path(__file__).resolve().parents[2]
    # Load only the launcher's functions, without starting the user's servers.
    command = r"""
        $ErrorActionPreference = 'Stop'
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            (Join-Path $PWD 'scripts/start-duemap.ps1'), [ref]$null, [ref]$null)
        $ast.FindAll({param($node)
            $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
        }, $false) | ForEach-Object { Invoke-Expression $_.Extent.Text }
        Wait-Endpoint 'http://127.0.0.1:PORT/api/health' -ApiHealth
    """.replace("PORT", str(server.server_port))
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=root, capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert requests == ["/api/health"] * 3
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
