"""View configured cameras through LeRobot. This script never opens motor ports."""
import argparse
import io
import json
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig


def main(check_only=False, no_browser=False):
    base = Path(__file__).resolve().parents[3]
    if not (base / "pyproject.toml").is_file():
        base = Path.cwd()
    (base / "outputs" / "camera_check").mkdir(parents=True, exist_ok=True)
    from cuk_robotics.config import load_hardware
    profiles = load_hardware(base / "configs" / "local" / "hardware.json", base)["robot"]["cameras"]
    cameras = {}
    try:
        for name, profile in profiles.items():
            options = {key: value for key, value in profile.items() if key != "type"}
            camera = OpenCVCamera(OpenCVCameraConfig(**options))
            camera.connect()
            cameras[name] = camera
            print(f"Connected: {name}, index={profile['index_or_path']}", flush=True)
        if check_only:
            counts = {name: 0 for name in cameras}
            previous = {name: None for name in cameras}
            start = time.perf_counter()
            while time.perf_counter() - start < 5:
                for name, camera in cameras.items():
                    camera.read_latest(max_age_ms=1000)
                    with camera.frame_lock:
                        timestamp = camera.latest_timestamp
                    if previous[name] != timestamp:
                        previous[name] = timestamp
                        counts[name] += 1
                time.sleep(0.005)
            elapsed = time.perf_counter() - start
            for name, camera in cameras.items():
                Image.fromarray(camera.read_latest()).save(base / "outputs" / "camera_check" / f"{name}.png")
                print(f"{name}: observed updates approximately {counts[name] / elapsed:.1f} Hz", flush=True)
        else:
            labels = {"left_wrist": "왼쪽 손목", "right_wrist": "오른쪽 손목", "top": "전체 시야"}
            panels = "".join(f'<section><h2>{labels.get(name, name)}</h2><img src="/stream/{name}"></section>' for name in cameras)
            html = ('<!doctype html><html lang="ko"><meta charset="utf-8"><title>SO-101 카메라 미리보기</title>'
                    '<style>body{font-family:system-ui;background:#10151c;color:#edf1f6;margin:24px}'
                    'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}'
                    'section{background:#1c2633;padding:16px;border-radius:12px}img{width:100%;display:block}'
                    'h2{font-size:20px;margin:0 0 12px}p{color:#bac7d6}</style>'
                    '<h1>카메라 미리보기</h1><p>종료: 실행 창에서 Ctrl+C. 원격조작을 시작하기 전에 미리보기를 종료하세요.</p>'
                    f'<main>{panels}</main></html>').encode("utf-8")

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    if self.path == "/":
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(html)
                        return
                    name = self.path.removeprefix("/stream/")
                    if not self.path.startswith("/stream/") or name not in cameras:
                        self.send_error(404)
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    try:
                        while True:
                            buffer = io.BytesIO()
                            Image.fromarray(cameras[name].read_latest()).save(buffer, format="JPEG", quality=80)
                            data = buffer.getvalue()
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(data)).encode() + b"\r\n\r\n" + data + b"\r\n")
                            self.wfile.flush()
                            time.sleep(1 / 30)
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, RuntimeError, TimeoutError):
                        pass

            with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
                url = f"http://127.0.0.1:{server.server_port}"
                (base / "outputs" / "camera_check" / "preview_url.txt").write_text(url, encoding="utf-8")
                print(f"Camera preview: {url}. Stop with Ctrl+C.", flush=True)
                if not no_browser:
                    webbrowser.open(url)
                server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for camera in cameras.values():
            if camera.is_connected:
                camera.disconnect()


def entrypoint():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    options = parser.parse_args()
    main(options.check_only, options.no_browser)


if __name__ == "__main__":
    entrypoint()
