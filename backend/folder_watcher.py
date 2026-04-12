"""폴더 감시 — Voca_8000/Lesson_XX/ 에 이미지 추가 시 자동 OCR 실행."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

log = logging.getLogger(__name__)

import httpx
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

IMAGE_EXTS = {".heic", ".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class LessonImageHandler(FileSystemEventHandler):
    def __init__(self, voca_root: Path, api_base: str = "http://127.0.0.1:8000"):
        self.voca_root = voca_root
        self.api_base = api_base.rstrip("/")
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in IMAGE_EXTS:
            return
        lesson_dir = path.parent
        # Lesson_XX 폴더가 voca_root 바로 아래여야 함
        if lesson_dir.parent.resolve() != self.voca_root.resolve():
            return
        # data.json이 이미 있으면 무시 (수동 수정 보호)
        if (lesson_dir / "data.json").exists():
            return
        self._schedule(lesson_dir.name)

    def _schedule(self, lesson_name: str):
        """파일이 여러 장 복사될 때를 위해 5초 디바운스."""
        with self._lock:
            existing = self._timers.get(lesson_name)
            if existing:
                existing.cancel()
            t = threading.Timer(5.0, self._trigger, args=[lesson_name])
            self._timers[lesson_name] = t
            t.start()

    def _trigger(self, lesson_name: str):
        with self._lock:
            self._timers.pop(lesson_name, None)
        log.info("새 이미지 감지 → %s OCR 시작…", lesson_name)
        try:
            resp = httpx.post(
                f"{self.api_base}/api/lessons/ingest_disk/{lesson_name}",
                timeout=300.0,
            )
            if resp.status_code == 200:
                d = resp.json()
                log.info("%s 완료: %d개 단어, %d장 처리",
                         lesson_name, d.get("words", 0), d.get("images_processed", 0))
            else:
                log.warning("%s 오류 %d: %s", lesson_name, resp.status_code, resp.text[:200])
        except Exception as e:
            log.error("%s 요청 실패: %s", lesson_name, e)


def start_watcher(voca_root: Path, api_base: str = "http://127.0.0.1:8000") -> Observer:
    voca_root.mkdir(parents=True, exist_ok=True)
    handler = LessonImageHandler(voca_root, api_base)
    observer = Observer()
    observer.schedule(handler, str(voca_root), recursive=True)
    observer.start()
    log.info("폴더 감시 시작: %s", voca_root)
    return observer
