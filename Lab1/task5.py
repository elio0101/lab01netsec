from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

last_token = ""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global last_token
        req = urlparse(self.path)

        if req.path == '/':
            self.send_response(200)
            self.end_headers()

        elif req.path == '/claim':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(last_token.encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global last_token
        req = urlparse(self.path)

        if req.path == '/claim':
            try:
                length = int(self.headers.get('Content-Length', 0))
                last_token = self.rfile.read(length).decode('utf-8')
                self.send_response(200)
                self.end_headers()
            except Exception:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8090), Handler)
    server.serve_forever()