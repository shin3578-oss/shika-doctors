# -*- coding: utf-8 -*-
"""docs/ の主要ページをPC幅で撮る。 python shot.py"""
import os, sys, http.server, socketserver, threading, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
SHOTS = os.path.join(ROOT, "_shots")
PORT = 8765
# base_path が /shika-doctors なので、その名前で配信する仮ルートを作る
os.makedirs(SHOTS, exist_ok=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

PAGES = [
    ("top", "/"),
    ("clinic", "/clinic/osaki-ovalcourt-dental/"),
    ("city", "/tokyo/shinagawa/"),
    ("entry", "/entry/"),
    ("feature", "/feature/"),
    ("about", "/about/"),
]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    for name, path in PAGES:
        pg.goto(f"http://127.0.0.1:{PORT}/shika-doctors{path}", wait_until="networkidle")
        pg.screenshot(path=os.path.join(SHOTS, f"{name}.png"), full_page=True)
        print("shot:", name, path)
    b.close()
httpd.shutdown()
