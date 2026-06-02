#!/usr/bin/env python3
"""
Kangaroo Ecolier PDF Question Extractor
Supports 4 PDF formats and image-only PDFs (stub mode).

Usage:
    python3 scripts/kangaroo_extract_questions.py [--dry-run] [--set SET_ID] [--level ecolier]
"""
import json
import re
import argparse
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

ROOT = Path(__file__).parent.parent
PDF_DIR = ROOT / "frontend" / "static" / "math" / "kangaroo" / "pdf"
JSON_DIR = ROOT / "backend" / "data" / "math" / "kangaroo"

IMAGE_KEYWORDS = [
    "picture", "shown", "figure", "diagram", "image",
    "the right", "below", "above", "following",
    "chart", "graph", "table", "grid", "map",
    "piece", "arrow", "fold", "rotate", "mirror", "sticker",
    "clock", "ruler", "pattern", "coin", "maze",
    "shape", "cut", "glue",
]

OCR_FIXES = [
    (r'\(8\)', '(B)'),
    (r'\{B\}', '(B)'),
    (r'\(e\)', '(C)'),
    (r'\{e\}', '(C)'),
    (r'\{D\}', '(D)'),
    (r'\{A\}', '(A)'),
]

HEADER_PATTERNS = [
    r'\d+(?:st|nd|rd|th) INTERNATIONAL.*?\n',
    r'KSF\s*[-–]\s*(?:finalized\s+)?[Pp]roblems.*?\n',
    r'KSF\s*-\s*Problems.*?\n',
    r'Time Allowed:.*?\n',
    r'--\s*\d+\s*of\s*\d+\s*--\n?',
    r'INTERNATIONAL KANGAROO MATHEMATICS CONTEST.*?\n',
    r'Level Ecolier.*?\n',
    r'Page \d+ of \d+\n',
    r'Math Kangaroo.*?\n',
    r'Kangaroo \d{4}.*?\n',
    r'Year \d+ and \d+.*?\n',
    r'\d+ points?\n',
    r'3 points?\n',
    r'4 points?\n',
    r'5 points?\n',
    r'-\s*\d+ point questions?\s*-\s*\n',
]


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return list of (1-indexed page number, raw text)."""
    doc = fitz.open(str(pdf_path))
    return [(i + 1, page.get_text()) for i, page in enumerate(doc)]


def clean_raw(text: str) -> str:
    for p, r in OCR_FIXES:
        text = re.sub(p, r, text)
    for p in HEADER_PATTERNS:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    return text


def is_image_required(text: str, options: dict) -> bool:
    lower = text.lower()
    # If options are all empty it's likely all-image
    opts_empty = not any(v.strip() for v in options.values())
    return opts_empty or any(kw in lower for kw in IMAGE_KEYWORDS)


def guess_topic(text: str, image_req: bool) -> str:
    lower = text.lower()
    if any(w in lower for w in ["how many", "total", "sum", "count", "number of", "weigh"]):
        return "arithmetic"
    if any(w in lower for w in ["fold", "rotate", "mirror", "shape", "circle", "square",
                                  "triangle", "rectangle"]):
        return "geometry"
    if any(w in lower for w in ["pattern", "sequence", "next", "series", "row", "column"]):
        return "pattern"
    if any(w in lower for w in ["order", "arrange", "different", "ways", "possible",
                                  "permut", "combinations"]):
        return "combinatorics"
    if any(w in lower for w in ["logic", "true", "false", "always", "never", "if"]):
        return "logic"
    if image_req:
        return "spatial_reasoning"
    return "arithmetic"


def detect_format(full_text: str) -> str:
    """Detect PDF question format."""
    if re.search(r'^#\s*\d+\.', full_text, re.MULTILINE):
        return "hash_dot"        # # N. text
    if re.search(r'^\d+\)', full_text, re.MULTILINE):
        return "paren_close"     # N) text with A) B) options
    if re.search(r'^[A-C]\d+\b', full_text, re.MULTILINE):
        return "leb_alpha"       # A1, B2, C3 style
    if re.search(r'^\d+\.', full_text, re.MULTILINE):
        return "dot"             # N. text (standard)
    return "unknown"


def build_q_lookup(sections_meta: list) -> tuple[dict, dict]:
    q_points: dict[str, int] = {}
    q_section: dict[str, int] = {}
    for sec_idx, sec in enumerate(sections_meta):
        pts = sec.get("points", 3)
        for q in sec.get("questions", []):
            q_points[str(q)] = pts
            q_section[str(q)] = sec_idx + 1
    return q_points, q_section


def char_to_page(offset: int, page_starts: dict) -> int:
    best = 1
    for start, pnum in sorted(page_starts.items()):
        if start <= offset:
            best = pnum
    return best


def build_full_text(pages: list[tuple[int, str]]) -> tuple[str, dict]:
    full = ""
    starts: dict[int, int] = {}
    for pnum, text in pages:
        starts[len(full)] = pnum
        full += clean_raw(text) + "\n"
    return full, starts


def parse_opt_paren(letter: str, chunk: str) -> str:
    m = re.search(rf'\({letter}\)\s*([^\n(]+)', chunk)
    return m.group(1).strip() if m else ""


def parse_opt_bare(letter: str, chunk: str) -> str:
    m = re.search(rf'\b{letter}\)\s*([^\nABCDE]+)', chunk)
    return m.group(1).strip() if m else ""


def extract_dot_format(full_text: str, answers: dict, q_points: dict, q_section: dict,
                        page_starts: dict) -> list[dict]:
    """Format: N. text\n(A) opt\n(B) opt..."""
    matches = list(re.finditer(r'(?m)^(?:#\s*)?(\d+)\.\s+', full_text))
    questions = []
    for idx, match in enumerate(matches):
        q_num = int(match.group(1))
        if q_num < 1 or q_num > 30:
            continue
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        block = full_text[start:end]
        pdf_page = char_to_page(start, page_starts)

        opt_m = re.search(r'\(A\)', block)
        if opt_m:
            q_text = re.sub(r'^(?:#\s*)?\d+\.\s+', '', block[:opt_m.start()], count=1)
            opts_raw = block[opt_m.start():]
            options = {L: parse_opt_paren(L, opts_raw) for L in "ABCDE"}
        else:
            q_text = re.sub(r'^(?:#\s*)?\d+\.\s+', '', block, count=1)
            options = {L: "" for L in "ABCDE"}

        q_text = re.sub(r'\s+', ' ', q_text).strip()
        image_req = is_image_required(q_text, options)
        correct = answers.get(str(q_num), "")
        topic = guess_topic(q_text, image_req)

        questions.append({
            "number": q_num,
            "section": q_section.get(str(q_num), 1),
            "points": q_points.get(str(q_num), 3),
            "pdf_page": pdf_page,
            "image_required": image_req,
            "question_text": q_text,
            "options": options,
            "answer": correct,
            "solution": (f"See PDF page {pdf_page} for the figure. Correct answer: {correct}."
                         if image_req else f"Work through the problem. Answer: {correct}."),
            "solution_steps": [],
            "difficulty": "",
            "topic": topic,
        })
    return questions


def extract_paren_close_format(full_text: str, answers: dict, q_points: dict, q_section: dict,
                                page_starts: dict) -> list[dict]:
    """Format: N) text\nA) opt  B) opt  C) opt  D) opt\nE) opt"""
    matches = list(re.finditer(r'(?m)^(\d+)\)\s+', full_text))
    questions = []
    for idx, match in enumerate(matches):
        q_num = int(match.group(1))
        if q_num < 1 or q_num > 30:
            continue
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        block = full_text[start:end]
        pdf_page = char_to_page(start, page_starts)

        # Options in bare "A) ... B) ..." form
        opt_m = re.search(r'\bA\)', block)
        if opt_m:
            q_text = re.sub(r'^\d+\)\s+', '', block[:opt_m.start()], count=1)
            opts_raw = block[opt_m.start():]
            options = {L: parse_opt_bare(L, opts_raw) for L in "ABCDE"}
        else:
            q_text = re.sub(r'^\d+\)\s+', '', block, count=1)
            options = {L: "" for L in "ABCDE"}

        q_text = re.sub(r'\s+', ' ', q_text).strip()
        image_req = is_image_required(q_text, options)
        correct = answers.get(str(q_num), "")
        topic = guess_topic(q_text, image_req)

        questions.append({
            "number": q_num,
            "section": q_section.get(str(q_num), 1),
            "points": q_points.get(str(q_num), 3),
            "pdf_page": pdf_page,
            "image_required": image_req,
            "question_text": q_text,
            "options": options,
            "answer": correct,
            "solution": (f"See PDF page {pdf_page} for the figure. Correct answer: {correct}."
                         if image_req else f"Work through the problem. Answer: {correct}."),
            "solution_steps": [],
            "difficulty": "",
            "topic": topic,
        })
    return questions


def extract_leb_format(full_text: str, answers: dict, q_points: dict, q_section: dict,
                        page_starts: dict) -> list[dict]:
    """Format: A1 ... (A) (B)... / B1... / C1..."""
    section_map = {"A": 1, "B": 2, "C": 3}
    matches = list(re.finditer(r'(?m)^([ABC])(\d+)\s+', full_text))
    questions = []
    q_counter = 0
    for idx, match in enumerate(matches):
        sec_letter = match.group(1)
        sec_num_in_sec = int(match.group(2))
        q_counter += 1
        q_num = q_counter
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        block = full_text[start:end]
        pdf_page = char_to_page(start, page_starts)

        opt_m = re.search(r'\(A\)', block)
        if opt_m:
            q_text = block[:opt_m.start()].strip()
            opts_raw = block[opt_m.start():]
            options = {L: parse_opt_paren(L, opts_raw) for L in "ABCDE"}
        else:
            q_text = block.strip()
            options = {L: "" for L in "ABCDE"}

        q_text = re.sub(r'^[ABC]\d+\s+', '', q_text).strip()
        q_text = re.sub(r'\s+', ' ', q_text).strip()
        image_req = is_image_required(q_text, options)
        correct = answers.get(str(q_num), "")
        topic = guess_topic(q_text, image_req)
        sec_idx = section_map.get(sec_letter, 1)

        questions.append({
            "number": q_num,
            "section": sec_idx,
            "points": q_points.get(str(q_num), 3),
            "pdf_page": pdf_page,
            "image_required": image_req,
            "question_text": q_text,
            "options": options,
            "answer": correct,
            "solution": (f"See PDF page {pdf_page} for the figure. Correct answer: {correct}."
                         if image_req else f"Work through the problem. Answer: {correct}."),
            "solution_steps": [],
            "difficulty": "",
            "topic": topic,
        })
    return questions


def make_image_stubs(answers: dict, sections_meta: list, total_pages: int) -> list[dict]:
    """For image-only PDFs: create stubs with page estimates."""
    q_points, q_section = build_q_lookup(sections_meta)
    total_q = sum(len(s.get("questions", [])) for s in sections_meta)
    if total_q == 0:
        total_q = len(answers)
    questions = []
    for q_str, correct in sorted(answers.items(), key=lambda x: int(x[0])):
        q_num = int(q_str)
        # Rough page estimate: distribute questions evenly across pages
        pdf_page = max(1, round((q_num - 1) / max(total_q, 1) * total_pages) + 1)
        questions.append({
            "number": q_num,
            "section": q_section.get(q_str, 1),
            "points": q_points.get(q_str, 3),
            "pdf_page": pdf_page,
            "image_required": True,
            "question_text": "",
            "options": {L: "" for L in "ABCDE"},
            "answer": correct,
            "solution": f"See PDF page {pdf_page} for this question. Correct answer: {correct}.",
            "solution_steps": [],
            "difficulty": "",
            "topic": "spatial_reasoning",
        })
    return questions


def extract_questions(pdf_path: Path, answers: dict, sections_meta: list) -> list[dict]:
    pages = extract_pdf_pages(pdf_path)
    total_pages = len(pages)
    total_text = sum(len(t) for _, t in pages)

    if total_text < 200:
        # Image-only PDF: create stubs
        return make_image_stubs(answers, sections_meta, total_pages)

    full_text, page_starts = build_full_text(pages)
    fmt = detect_format(full_text)
    q_points, q_section = build_q_lookup(sections_meta)

    if fmt in ("dot", "hash_dot"):
        qs = extract_dot_format(full_text, answers, q_points, q_section, page_starts)
    elif fmt == "paren_close":
        qs = extract_paren_close_format(full_text, answers, q_points, q_section, page_starts)
    elif fmt == "leb_alpha":
        qs = extract_leb_format(full_text, answers, q_points, q_section, page_starts)
    else:
        qs = []

    # If extraction got wrong count, fall back to stubs
    extracted_nums = {q["number"] for q in qs}
    # Only compare numeric answer keys
    expected_nums = {int(k) for k in answers if k.isdigit()}
    missing = expected_nums - extracted_nums

    # Remove questions with wrong numbers (only for numeric keys)
    if expected_nums:
        qs = [q for q in qs if q["number"] in expected_nums]
        # Add stubs for missing questions
        if missing:
            stubs = make_image_stubs(
                {k: v for k, v in answers.items()
                 if k.isdigit() and int(k) in missing},
                sections_meta, total_pages
            )
            qs.extend(stubs)
    else:
        # Alpha-keyed answers (e.g., leb): limit to answer count
        qs = qs[:len(answers)]

    # Deduplicate: keep first occurrence of each question number
    seen: set[int] = set()
    deduped = []
    for q in sorted(qs, key=lambda q: q["number"]):
        if q["number"] not in seen:
            seen.add(q["number"])
            deduped.append(q)
    return deduped


def process_set(set_id: str, dry_run: bool = False) -> bool:
    json_path = JSON_DIR / f"{set_id}.json"
    if not json_path.exists():
        print(f"  SKIP: {json_path} not found")
        return False

    data = json.loads(json_path.read_text())
    pdf_file = data.get("pdf_file", "")
    answers = data.get("answers", {})
    sections_meta = data.get("sections_meta", [])

    if not answers:
        print(f"  SKIP {set_id}: no answers")
        return False

    if data.get("questions"):
        print(f"  SKIP {set_id}: already has {len(data['questions'])} questions")
        return False

    if not pdf_file:
        print(f"  SKIP {set_id}: no pdf_file")
        return False

    rel = pdf_file.lstrip("/")
    if rel.startswith("static/"):
        rel = rel[len("static/"):]
    pdf_path = ROOT / "frontend" / "static" / rel

    if not pdf_path.exists():
        print(f"  SKIP {set_id}: PDF not found ({pdf_path.name})")
        return False

    print(f"  {set_id} ({pdf_path.name})...", end=" ")
    questions = extract_questions(pdf_path, answers, sections_meta)
    print(f"{len(questions)} questions extracted")

    if not dry_run:
        data["questions"] = questions
        data["solutions_complete"] = False
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--set", help="Process one set_id")
    parser.add_argument("--level", default="ecolier")
    args = parser.parse_args()

    if args.set:
        process_set(args.set, dry_run=args.dry_run)
        return

    count = 0
    for json_path in sorted(JSON_DIR.glob("*.json")):
        try:
            data = json.loads(json_path.read_text())
        except Exception:
            continue
        if data.get("level") != args.level:
            continue
        if data.get("questions"):
            print(f"  SKIP {json_path.stem}: already has questions")
            continue
        if process_set(json_path.stem, dry_run=args.dry_run):
            count += 1

    print(f"\nDone. Processed {count} sets.")


if __name__ == "__main__":
    main()
