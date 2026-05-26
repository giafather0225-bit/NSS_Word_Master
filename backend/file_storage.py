"""File storage module — HEIC/PDF upload handling and storage/lessons/{lesson_id}/ management.

Storage path: ~/NSS_Learning/storage/lessons/{lesson_id}/
HEIC → JPG conversion: macOS sips (primary) / pillow-heif (optional fallback)
PDF: saved as scanned copy with page-count metadata.
"""

import io
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Optional

from backend.database import LEARNING_ROOT

STORAGE_ROOT = LEARNING_ROOT / "storage" / "lessons"

# Allowed extensions
ALLOWED_IMAGE_EXTS = {".heic", ".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_PDF_EXTS   = {".pdf"}
ALLOWED_EXTS       = ALLOWED_IMAGE_EXTS | ALLOWED_PDF_EXTS

# File size guard.
# Note: the HTTP router layer (files_common._stream_save_upload) already caps
# incoming uploads at 20 MB.  This constant is a defence-in-depth backstop
# for any direct programmatic call to save_lesson_file() outside HTTP context.
MAX_FILE_BYTES = 80 * 1024 * 1024

# Magic-byte signatures for image format verification.
# .heic/.heif omitted — their ISO Base Media "ftyp" box varies by encoder;
# Pillow/pillow-heif will reject malformed HEIC content.
_IMAGE_MAGIC: dict[str, list[bytes]] = {
    ".jpg":  [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png":  [b"\x89PNG\r\n\x1a\n"],
    ".webp": [b"RIFF"],
    ".gif":  [b"GIF87a", b"GIF89a"],
    ".bmp":  [b"BM"],
}


def _check_image_magic(raw: bytes, ext: str) -> bool:
    """Return True if ``raw`` starts with the expected magic bytes for ``ext``."""
    sigs = _IMAGE_MAGIC.get(ext, [])
    if not sigs:
        return True
    return any(raw[:12].startswith(s) for s in sigs)

_SAFE_FNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-. ]{0,99}$")


class FileRecord(TypedDict):
    filename: str          # stored filename (after any conversion)
    original_name: str     # original uploaded filename
    content_type: str      # MIME type of stored file
    size: int              # stored file size in bytes
    converted: bool        # True if HEIC was converted to JPG
    pages: Optional[int]   # PDF page count (None for images)
    path: str              # absolute filesystem path


def _lesson_dir(lesson_id: int) -> Path:
    d = STORAGE_ROOT / str(lesson_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_stem(name: str) -> str:
    """Strip dangerous characters from a filename to prevent path traversal."""
    stem = Path(name).stem
    safe = re.sub(r"[^A-Za-z0-9_\-. ]", "_", stem)[:80].strip("._- ")
    return safe or "upload"


def _heic_to_jpg_sips(raw: bytes) -> bytes:
    """Convert HEIC bytes to JPEG bytes using macOS sips."""
    with tempfile.NamedTemporaryFile(suffix=".heic", delete=False) as src_f:
        src_path = Path(src_f.name)
        src_f.write(raw)

    dst_path = src_path.with_suffix(".jpg")
    try:
        subprocess.run(
            ["sips", "-s", "format", "jpeg", str(src_path), "--out", str(dst_path)],
            check=True,
            capture_output=True,
        )
        return dst_path.read_bytes()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"HEIC conversion failed (sips): {e.stderr.decode(errors='replace')}") from e
    finally:
        src_path.unlink(missing_ok=True)
        dst_path.unlink(missing_ok=True)


def _heic_to_jpg(raw: bytes) -> bytes:
    """Try pillow-heif first; fall back to sips if unavailable."""
    try:
        import pillow_heif                          # type: ignore[import]
        from PIL import Image                       # type: ignore[import]
        pillow_heif.register_heif_opener()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except ImportError:
        return _heic_to_jpg_sips(raw)


def _pdf_page_count(raw: bytes) -> Optional[int]:
    """Return PDF page count; None if pymupdf is unavailable or parsing fails."""
    try:
        import fitz                                 # type: ignore[import]
        doc = fitz.open(stream=raw, filetype="pdf")
        return doc.page_count
    except ImportError:
        pass
    except (ValueError, RuntimeError, OSError):
        return None
    # Lightweight fallback: scan raw bytes for /Count entries.
    try:
        text = raw.decode("latin-1", errors="replace")
        counts = re.findall(r"/Count\s+(\d+)", text)
        if counts:
            return max(int(c) for c in counts)
    except (UnicodeDecodeError, ValueError, OverflowError):
        pass
    return None


def _index_path(lesson_id: int) -> Path:
    return _lesson_dir(lesson_id) / "_index.json"


def _load_index(lesson_id: int) -> list[dict]:
    p = _index_path(lesson_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_index(lesson_id: int, index: list[dict]) -> None:
    _index_path(lesson_id).write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────

def save_lesson_file(lesson_id: int, raw: bytes, original_name: str) -> FileRecord:
    """파일을 storage/lessons/{lesson_id}/ 에 저장.

    - HEIC → JPG 자동 변환 후 저장
    - PDF → 그대로 저장 (스캔본 보존), 페이지 수 기록
    - 중복 파일명: _1, _2 suffix로 자동 처리
    """
    if len(raw) == 0:
        raise ValueError("빈 파일입니다.")
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError(f"파일 크기 초과 (최대 {MAX_FILE_BYTES // 1024 // 1024} MB)")

    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"허용되지 않는 파일 형식: {ext or '(없음)'}")

    stem = _safe_stem(original_name)
    converted = False
    pages: Optional[int] = None
    content_type: str

    if ext in ALLOWED_IMAGE_EXTS:
        if ext == ".heic":
            raw = _heic_to_jpg(raw)
            ext = ".jpg"
            converted = True
        elif not _check_image_magic(raw, ext):
            raise ValueError(f"파일 내용이 확장자({ext})와 일치하지 않습니다.")
        content_type = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext.lstrip('.')}"

    else:  # PDF
        if not raw.startswith(b"%PDF"):
            raise ValueError("유효한 PDF 파일이 아닙니다.")
        pages = _pdf_page_count(raw)
        content_type = "application/pdf"

    # 중복 파일명 처리
    lesson_dir = _lesson_dir(lesson_id)
    target = lesson_dir / f"{stem}{ext}"
    counter = 1
    while target.exists():
        target = lesson_dir / f"{stem}_{counter}{ext}"
        counter += 1

    target.write_bytes(raw)

    record: FileRecord = {
        "filename":      target.name,
        "original_name": original_name,
        "content_type":  content_type,
        "size":          len(raw),
        "converted":     converted,
        "pages":         pages,
        "path":          str(target),
    }

    # _index.json 업데이트
    index = _load_index(lesson_id)
    index.append({
        **record,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_index(lesson_id, index)

    return record


def list_lesson_files(lesson_id: int) -> list[dict]:
    """저장된 파일 목록 반환 (_index.json 기반, 실제 파일 존재 여부 검증)."""
    index = _load_index(lesson_id)
    valid = []
    changed = False
    for entry in index:
        if Path(entry.get("path", "")).exists():
            valid.append(entry)
        else:
            changed = True  # 삭제된 파일은 인덱스에서 제거
    if changed:
        _save_index(lesson_id, valid)
    return valid


def delete_lesson_file(lesson_id: int, filename: str) -> bool:
    """파일 삭제. 성공 여부 반환."""
    if not _SAFE_FNAME_RE.match(filename):
        raise ValueError("유효하지 않은 파일명")

    lesson_dir = _lesson_dir(lesson_id)
    target = lesson_dir / filename

    # 경로 이탈 방지
    if lesson_dir not in target.parents and target.parent != lesson_dir:
        raise ValueError("유효하지 않은 파일 경로")

    if not target.exists():
        return False

    target.unlink()

    index = [e for e in _load_index(lesson_id) if e.get("filename") != filename]
    _save_index(lesson_id, index)
    return True
