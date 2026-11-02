"""A complete REST-style server in one file, using only the standard library.

It exists to show what a framework such as FastAPI does for us later.
Run from the project root: python experiments/tiny_server.py
Then in a second terminal: curl -i http://127.0.0.1:8000/api/issues
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

ISSUES = {
    1: {"id": 1, "title": "Login page is blank", "status": "open"},
    2: {"id": 2, "title": "Export is slow", "status": "in_progress"},
}


class IssueHandler(BaseHTTPRequestHandler):
    def send_json(self, status: int, data) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/issues":
            self.send_json(200, list(ISSUES.values()))
        elif self.path.startswith("/api/issues/"):
            issue = ISSUES.get(self.issue_id_from_path())
            if issue is None:
                self.send_json(404, {"detail": "issue not found"})
            else:
                self.send_json(200, issue)
        else:
            self.send_json(404, {"detail": "no such address"})

    def do_POST(self) -> None:
        if self.path != "/api/issues":
            self.send_json(404, {"detail": "no such address"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            title = data["title"]
        except json.JSONDecodeError, KeyError:
            self.send_json(422, {"detail": "send JSON with a title"})
            return
        new_id = max(ISSUES) + 1
        ISSUES[new_id] = {"id": new_id, "title": title, "status": "open"}
        self.send_json(201, ISSUES[new_id])

    def issue_id_from_path(self) -> int:
        text = self.path.rsplit("/", maxsplit=1)[-1]
        return int(text) if text.isdigit() else 0


if __name__ == "__main__":
    print("Listening on http://127.0.0.1:8000 (press Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", 8000), IssueHandler).serve_forever()
