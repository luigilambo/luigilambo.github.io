#!/usr/bin/env python3
"""Static server for the fully-independent shader.se mirror.

Serves everything locally — no third-party requests:
- ignores the ?dpl=… query Next.js appends to chunk URLs
- /mux/…        local HLS (m3u8 + .ts) downloaded from Mux  (replaces stream.mux.com)
- /draco/…      local Draco decoder                          (replaces gstatic.com)
- /_a/…         analytics no-op (empty script + 204 on send) (replaces analytics.shader.build)
- /api/mux-image/…  project carousel posters (+ fallback for ids we didn't mirror)
"""
import http.server, socketserver, os, urllib.parse, mimetypes

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror_root")
FALLBACK = os.path.join(ROOT, "textures", "thumb_fallback.png")
PORT = 8300

mimetypes.add_type("application/vnd.apple.mpegurl", ".m3u8")
mimetypes.add_type("video/mp2t", ".ts")
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("image/svg+xml", ".svg")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def translate_path(self, path):
        path = urllib.parse.urlparse(path).path          # drop ?query / #frag
        return super().translate_path(path)

    def guess_type(self, path):
        if "/api/mux-image/" in path.replace(os.sep, "/"):
            return "image/jpeg"
        return super().guess_type(path)

    def _send_bytes(self, data, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def do_GET(self):
        clean = urllib.parse.urlparse(self.path).path

        # analytics no-op
        if clean.startswith("/_a/"):
            if clean.endswith("/api/send"):
                self._send_bytes(b"", "text/plain", 200)
            else:                                          # /_a/script.js -> empty JS
                self._send_bytes(b"/* analytics disabled in local mirror */",
                                 "application/javascript", 200)
            return

        # mux-image poster fallback for ids we didn't mirror
        if clean.startswith("/api/mux-image/") and not os.path.isfile(self.translate_path(self.path)):
            try:
                with open(FALLBACK, "rb") as f:
                    self._send_bytes(f.read(), "image/png", 200)
                return
            except Exception:
                pass

        super().do_GET()

    def do_POST(self):                                     # analytics send is a POST
        clean = urllib.parse.urlparse(self.path).path
        if clean.startswith("/_a/"):
            self._send_bytes(b"", "text/plain", 200)
            return
        self.send_error(404)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        # local dev mirror: never cache, so swapped assets show up on reload
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"serving fully-independent mirror at http://127.0.0.1:{PORT}")
    httpd.serve_forever()
