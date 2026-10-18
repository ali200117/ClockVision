import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from visionclock_ml import api_client, config


class FakeBackend(BaseHTTPRequestHandler):
    def _reply(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/employees/1":
            self._reply(200, {"id": 1, "firstName": "Ali", "lastName": "Test"})
        else:
            self._reply(404, {"title": "Employee not found", "detail": "Employee with id 9 not found"})

    def do_POST(self):
        if self.path == "/api/employees/1/clock":
            self._reply(201, {"id": 10, "employeeId": 1, "type": "CLOCK_IN"})
        else:
            self._reply(409, {"detail": "Employee with id 2 is deactivated"})

    def log_message(self, *args):
        pass


@pytest.fixture()
def backend(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeBackend)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(config, "BACKEND_URL", f"http://127.0.0.1:{server.server_port}")
    yield
    server.shutdown()


def test_get_employee(backend):
    assert api_client.get_employee(1)["firstName"] == "Ali"


def test_clock_returns_event(backend):
    assert api_client.clock(1)["type"] == "CLOCK_IN"


def test_error_response_becomes_backend_error_with_detail(backend):
    with pytest.raises(api_client.BackendError, match="deactivated"):
        api_client.clock(2)


def test_unreachable_backend_becomes_backend_error(monkeypatch):
    monkeypatch.setattr(config, "BACKEND_URL", "http://127.0.0.1:1")
    with pytest.raises(api_client.BackendError):
        api_client.get_employee(1)
