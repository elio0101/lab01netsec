import socketserver

store = {}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            line = self.rfile.readline()
            if not line:
                break
            try:
                req = line.decode('ascii')
                if not req.endswith('\n'):
                    break
                req = req[:-1]

                parts = req.split(' ', 1)
                cmd = parts[0]

                res = "ERR"

                if cmd == "PING" and len(parts) == 1:
                    res = "PONG"
                elif cmd == "ECHO" and len(parts) == 2:
                    res = parts[1]
                elif cmd == "SET" and len(parts) == 2:
                    kv = parts[1].split(' ', 1)
                    if len(kv) == 2:
                        store[kv[0]] = kv[1]
                        res = "OK"
                elif cmd == "GET" and len(parts) == 2:
                    k = parts[1]
                    if ' ' not in k:
                        res = store.get(k, "NOT_FOUND")

                self.wfile.write((res + "\n").encode('ascii'))
            except Exception:
                self.wfile.write(b"ERR\n")


socketserver.ThreadingTCPServer.allow_reuse_address = True
server = socketserver.ThreadingTCPServer(("0.0.0.0", 9001), Handler)
server.serve_forever()