import hashlib
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve


async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    method = scope['method']
    path = scope['path']
    http_version = scope.get('http_version', '1.1')

    if method == 'GET' and path == '/':
        headers = [(b'content-type', b'text/plain')]
        if http_version != '3':
            headers.append((b'alt-svc', b'h3=":4433"'))

        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': headers
        })
        await send({'type': 'http.response.body', 'body': b''})

    elif method == 'GET' and path == '/proto':
        body = f"HTTP/{http_version}".encode('utf-8')
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/plain')]
        })
        await send({'type': 'http.response.body', 'body': body})

    elif method == 'POST' and path == '/hash':
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)

        digest = hashlib.sha256(body).hexdigest().encode('utf-8')
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/plain')]
        })
        await send({'type': 'http.response.body', 'body': digest})

    else:
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': []
        })
        await send({'type': 'http.response.body', 'body': b''})


if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:4433"]
    config.quic_bind = ["0.0.0.0:4433"]
    config.certfile = "server.crt"
    config.keyfile = "server.key"
    config.alpn_protocols = ["h3", "h2", "http/1.1"]
    asyncio.run(serve(app, config))