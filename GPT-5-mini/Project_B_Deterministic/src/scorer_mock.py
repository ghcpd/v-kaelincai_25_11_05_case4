import time
import threading
import random
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class ScorerHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        payload = self.rfile.read(length).decode()
        try:
            req = json.loads(payload)
        except Exception:
            self._send_json({'error':'bad json'},400)
            return
        cfg = self.server.cfg
        delay = max(0, random.gauss(cfg['mean_ms']/1000.0, cfg['std_ms']/1000.0))
        time.sleep(delay)
        if random.random() < cfg.get('fail_rate',0):
            self._send_json({'error':'scorer failure'},500)
            return
        base = sum((ord(c)%5) for c in req.get('answer',''))
        if cfg.get('flaky', False) and random.random() < cfg.get('flaky_rate',0.3):
            base += random.choice([-2,-1,1,2])
        resp = {'q':req.get('q'), 'score': base}
        self._send_json(resp)

    def log_message(self, format, *args):
        return

def run_mock(host='127.0.0.1', port=9000, cfg=None):
    if cfg is None:
        cfg = {'mean_ms':100,'std_ms':40,'fail_rate':0.0,'flaky':True,'flaky_rate':0.3}
    server = HTTPServer((host, port), ScorerHandler)
    server.cfg = cfg
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Scorer mock running on http://{host}:{port} with cfg={cfg}")
    return server
