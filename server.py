#!/usr/bin/env python3
"""
Ollama Studio Web Server & Reverse Proxy
Serves static UI files and proxies /api/* requests to local Ollama daemon (127.0.0.1:11434).
Allows secure remote access via ngrok/tunnels without CORS or Mixed Content errors.
"""

import sys
import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

OLLAMA_BACKEND = "http://127.0.0.1:11434"
DEFAULT_PORT = 3300

class OllamaProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for all responses
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.proxy_request("DELETE")
        else:
            self.send_error(404, "Not Found")

    def proxy_request(self, method):
        target_url = f"{OLLAMA_BACKEND}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target_url, data=body, method=method)
        for h, v in self.headers.items():
            if h.lower() not in ["host", "content-length"]:
                req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                self.send_response(resp.status)
                for h, v in resp.getheaders():
                    if h.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(h, v)
                self.end_headers()

                # Stream response chunks immediately
                while True:
                    chunk = resp.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_data = json.dumps({"error": f"Ollama proxy error: {str(e)}"}).encode()
            self.wfile.write(err_data)

def run():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("0.0.0.0", port), OllamaProxyHandler)
    print(f"Ollama Studio server & proxy running on http://0.0.0.0:{port}")
    print(f"Forwarding /api/* -> {OLLAMA_BACKEND} (CORS & HTTPS-tunnel safe)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == "__main__":
    run()
