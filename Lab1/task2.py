import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

notes_db = {}
next_id = 1


class ApiHandler(BaseHTTPRequestHandler):
    def send_resp(self, code, payload=None):
        self.send_response(code)
        if payload is not None:
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        else:
            self.end_headers()

    def do_GET(self):
        req = urlparse(self.path)

        if req.path == '/':
            self.send_resp(200)

        elif req.path == '/echo':
            qs = parse_qs(req.query)
            msg = qs.get('msg', [''])[0]
            self.send_resp(200, {"msg": msg})

        elif req.path.startswith('/notes/'):
            parts = req.path.split('/')
            if len(parts) == 3:
                try:
                    nid = int(parts[2])
                except ValueError:
                    return self.send_resp(404)

                if nid in notes_db:
                    self.send_resp(200, {"id": nid, "text": notes_db[nid]})
                else:
                    self.send_resp(404)
            else:
                self.send_resp(404)

        else:
            self.send_resp(404)

    def do_POST(self):
        global next_id
        req = urlparse(self.path)

        if req.path == '/notes':
            if self.headers.get('Content-Type') != 'application/json':
                return self.send_resp(415)

            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)

                if 'text' not in data or type(data['text']) is not str:
                    return self.send_resp(400)
            except Exception:
                return self.send_resp(400)

            notes_db[next_id] = data['text']
            resp = {"id": next_id}
            next_id += 1
            self.send_resp(201, resp)

        else:
            self.send_resp(404)

    def do_DELETE(self):
        req = urlparse(self.path)

        if req.path.startswith('/notes/'):
            parts = req.path.split('/')
            if len(parts) == 3:
                try:
                    nid = int(parts[2])
                except ValueError:
                    return self.send_resp(404)

                if nid in notes_db:
                    del notes_db[nid]
                    self.send_resp(204)
                else:
                    self.send_resp(404)
            else:
                self.send_resp(404)
        else:
            self.send_resp(404)

    def handle_unsupported(self):
        if self.path == '/notes' or self.path.startswith('/notes/'):
            self.send_resp(405)
        else:
            self.send_resp(404)

    do_PUT = handle_unsupported
    do_PATCH = handle_unsupported


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ApiHandler)
    server.serve_forever()