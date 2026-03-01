import http.server
import socketserver
import os

PORT = 3004
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        pass  # suppress logs


with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving on port {PORT}", flush=True)
    httpd.serve_forever()
