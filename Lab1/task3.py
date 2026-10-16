import json
import ssl
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from http import cookies

sessions = {}


class BaseTlsHandler(BaseHTTPRequestHandler):
    def send_resp(self, code, payload=None, content_type='application/json', cookie=None):
        self.send_response(code)
        if payload is not None:
            self.send_header('Content-Type', content_type)
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()

        if payload is not None:
            if content_type == 'application/json':
                self.wfile.write(json.dumps(payload).encode('utf-8'))
            else:
                self.wfile.write(payload.encode('utf-8'))


class MainHandler(BaseTlsHandler):
    def do_GET(self):
        req = urlparse(self.path)

        if req.path == '/':
            self.send_resp(200)

        elif req.path == '/me':
            cookie_header = self.headers.get('Cookie')
            user = None
            if cookie_header:
                c = cookies.SimpleCookie(cookie_header)
                if 'session_id' in c:
                    sid = c['session_id'].value
                    user = sessions.get(sid)

            if user:
                self.send_resp(200, {"user": user})
            else:
                self.send_resp(401)
        else:
            self.send_resp(404)

    def do_POST(self):
        req = urlparse(self.path)

        if req.path == '/login':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)

                if data.get('password') == 'netsec' and 'user' in data:
                    sid = str(uuid.uuid4())
                    sessions[sid] = data['user']
                    cookie_val = f"session_id={sid}; Secure; HttpOnly"
                    self.send_resp(200, cookie=cookie_val)
                else:
                    self.send_resp(401)
            except Exception:
                self.send_resp(401)
        else:
            self.send_resp(404)


class MtlsHandler(BaseTlsHandler):
    def do_GET(self):
        req = urlparse(self.path)

        if req.path == '/whoami':
            cert = self.connection.getpeercert()
            cn = ""
            for sub in cert.get('subject', []):
                for key, val in sub:
                    if key == 'commonName':
                        cn = val
            self.send_resp(200, cn, content_type='text/plain')
        else:
            self.send_resp(404)


def run_8443():
    httpd = HTTPServer(('0.0.0.0', 8443), MainHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile="server.crt", keyfile="server.key")
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()


def run_8444():
    httpd = HTTPServer(('0.0.0.0', 8444), MtlsHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile="server.crt", keyfile="server.key")
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile="ca.crt")
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()


if __name__ == '__main__':
    threading.Thread(target=run_8443, daemon=True).start()
    run_8444()