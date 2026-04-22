"""
scripts/ckla_parser.py — CKLA G3 Teacher Anthology PDF parser
Section: Academy
Dependencies: pypdf
API: none (module imported by import script)

Extracts per-lesson structured data from CKLA G3 "Tell It Again!"
Read-Aloud Anthology PDFs:

    {
      "domain_title": "The Human Body: Systems and Senses",
      "lessons": [
        {
          "lesson_num": 1,
          "lesson_title": "Building Blocks and Systems",
          "vocabulary": ["cells", "circulate", "functions", ...],
          "passage": "Hello everybody. I'm Ricardo...",
          "questions": [
            {"kind": "Literal", "q": "What...", "model_a": "Muscles..."},
            ...
          ],
          "word_work_word": "interconnected"
        },
        ...
      ]
    }

Usage:
    from ckla_parser import parse_domain
    data = parse_domain("/tmp/ckla_g3/D3_Anth.pdf")
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pypdf


# @tag ACADEMY
def _page_lines(text: str) -> list[str]:
    """Split page text into lines, stripping boilerplate."""
    out: list[str] = []
    for ln in text.split("\n"):
        ls = ln.strip()
        if not ls:
            continue
        if "Core Knowledge Foundation" in ls:
            continue
        if re.match(r"^©\s*\d{4}", ls):
            continue
        # Standalone page numbers
        if re.match(r"^\d{1,3}$", ls):
            continue
        out.append(ls)
    return out


# @tag ACADEMY
def _detect_lesson_marker(page_text: str) -> Optional[tuple[int, str, str]]:
    """Return (lesson_num, 'A'|'B', lesson_title) if page belongs to a lesson section.

    CKLA page header format (varies slightly):
        "The Human Body: Systems and Senses 1A | Building Blocks and Systems 19"
        "18 The Human Body: Systems and Senses 1A | Building Blocks and Systems"
    """
    first = page_text.split("\n", 1)[0] if page_text else ""
    # Pattern: digit+ A|B then "|" then title
    m = re.search(r"\s(\d+)([AB])\s*\|\s*([^\n\d][^\n]*?)(?:\s+\d+)?$", first)
    if not m:
        return None
    num = int(m.group(1))
    part = m.group(2)
    title = m.group(3).strip()
    # Trim trailing page number if any residual
    title = re.sub(r"\s+\d+$", "", title).strip()
    return num, part, title


# @tag ACADEMY
def _collect_lesson_sections(reader: pypdf.PdfReader) -> dict[tuple[int, str], list[int]]:
    """Map (lesson_num, A|B) → sorted list of page indices (0-based)."""
    sections: dict[tuple[int, str], list[int]] = {}
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        marker = _detect_lesson_marker(text)
        if marker is None:
            continue
        num, part, _ = marker
        sections.setdefault((num, part), []).append(idx)
    return sections


# @tag ACADEMY
def _lesson_title(reader: pypdf.PdfReader, pages: list[int]) -> str:
    """Extract lesson title from first page header in the section."""
    for p in pages:
        text = reader.pages[p].extract_text() or ""
        marker = _detect_lesson_marker(text)
        if marker:
            return marker[2]
    return ""


# @tag ACADEMY
def _repair_split_words(text: str) -> str:
    """Fix PDF text-layer damage where a single leading capital is split from the
    rest of its word by a newline or stray space (e.g., 'L\\niteral' → 'Literal',
    'W ho' → 'Who'). Pattern is safe because natural English never has a bare
    capital letter followed by a lowercase word (sentences after line-breaks begin
    with a fully capitalized first word)."""
    # Only the newline variant is safe — "A\nbook" never occurs in clean English
    # since line-wrapped sentences begin with a fully capitalized next word.
    text = re.sub(r"\b([A-Z])\n([a-z]{2,})\b", r"\1\2", text)
    return text


# @tag ACADEMY
def _join_pages(reader: pypdf.PdfReader, pages: list[int]) -> str:
    raw = "\n".join(reader.pages[p].extract_text() or "" for p in sorted(pages))
    return _repair_split_words(raw)


# @tag ACADEMY
def _strip_page_headers(text: str, domain_title: str) -> str:
    """Remove repeating page-header lines that leak into extracted text."""
    out: list[str] = []
    for ln in text.split("\n"):
        ls = ln.strip()
        if not ls:
            continue
        # Skip header lines: "<domain> NA | <lesson> <pagenum>" or inverse
        if domain_title and domain_title in ls and re.search(r"\d+[AB]\s*\|", ls):
            continue
        if "Core Knowledge Foundation" in ls:
            continue
        if re.match(r"^©\s*\d{4}", ls):
            continue
        if re.match(r"^\d{1,3}\s+" + re.escape(domain_title), ls) if domain_title else False:
            continue
        if re.match(r"^\d{1,3}$", ls):
            continue
        out.append(ls)
    return "\n".join(out)


# @tag ACADEMY
def _extract_passage(section_text: str, lesson_title: str = "") -> str:
    """Isolate the read-aloud passage (between 'Presenting the Read-Aloud' and
    'Discussing the Read-Aloud'). Strip instructional bullets and 'Show image' cues."""
    start = section_text.find("Presenting the Read-Aloud")
    if start < 0:
        return ""
    # Jump past "Presenting the Read-Aloud 20 minutes" header line
    body_start = section_text.find("\n", start)
    body = section_text[body_start + 1:] if body_start > 0 else section_text[start:]

    end = body.find("Discussing the Read-Aloud")
    if end > 0:
        body = body[:end]

    # Remove Wingdings/private-use glyphs that leak as bullets
    body = re.sub(r"[\uf000-\uf8ff]", "", body)
    # Remove "Show image ..." captions
    body = re.sub(r"Show image [^\n]*\n?", "", body, flags=re.IGNORECASE)
    # Remove bracketed teacher stage directions, possibly spanning lines:
    #   [Pause for students to answer.]  [Show Image Card 1 (Types of Cells).]
    #   [Point to Ricardo's T-shirt.]
    body = re.sub(r"\[[^\[\]]{0,500}?\]", "", body, flags=re.DOTALL)
    # Remove leading numeric footnote markers like " 1 ", " 2 " on their own line
    body = re.sub(r"\n\s*\d{1,2}\s*\n", "\n", body)
    # Remove inline sidebar callouts: "\n<digit>\s+<sidebar text>" running until
    # a line that looks like normal narration. Sidebars appear after brackets get
    # stripped as orphan "14  What..." prefixes — drop the digit prefix.
    body = re.sub(r"(?m)^\s*\d{1,2}\s+(?=[A-Z])", "", body)

    cleaned_lines: list[str] = []
    for ln in body.split("\n"):
        ls = ln.strip()
        if not ls:
            continue
        # Skip sidebar note lines like "1 or groups of complex interconnected systems"
        if re.match(r"^\d+\s+(or|a|an|the|meaning|i\.e\.|e\.g\.)\b", ls, re.IGNORECASE):
            continue
        # Skip any remaining lines that are purely a sidebar number + short gloss
        # (digit followed by <= 10 words of lowercase gloss, no sentence terminator)
        if re.match(r"^\d+\s+[a-z]", ls) and len(ls.split()) <= 12 and not re.search(r"[.!?]$", ls):
            continue
        cleaned_lines.append(ls)
    result = "\n".join(cleaned_lines).strip()

    # Strip leading echo of the lesson title (CKLA prints the title as the passage's
    # first line, which duplicates the page-header line).
    if lesson_title:
        lt = lesson_title.strip()
        if result.lower().startswith(lt.lower()):
            result = result[len(lt):].lstrip("\n :—-").strip()
    return result


# @tag ACADEMY
def _extract_questions(section_text: str) -> list[dict]:
    """Extract Comprehension Questions list with kind (Literal/Inferential/Evaluative) + model answer."""
    start = section_text.find("Comprehension Questions")
    if start < 0:
        return []
    block = section_text[start:]
    end = block.find("Word Work")
    if end > 0:
        block = block[:end]

    # Strip bracketed stage directions (e.g., "[Show Poster 2 — Building Blocks]")
    block = re.sub(r"\[[^\[\]]{0,500}?\]", "", block, flags=re.DOTALL)
    # Remove Wingdings / private-use bullets
    block = re.sub(r"[\uf000-\uf8ff]", "", block)

    # Drop the instructional paragraph before question 1.
    m = re.search(r"\n\s*1\.\s*(Literal|Inferential|Evaluative)", block)
    if m:
        block = block[m.start():]

    # Split by question number markers "\n<num>. [✍] <Kind>"
    # CKLA sometimes inserts a writing icon (✍, U+270D) between "." and the kind.
    parts = re.split(
        r"\n\s*(\d+)\.\s*[\u270d\u2712\u270f\ufffd\*\s]*(Literal|Inferential|Evaluative)\b",
        block,
    )
    # parts = [prefix, num1, kind1, body1, num2, kind2, body2, ...]
    out: list[dict] = []
    for i in range(1, len(parts), 3):
        try:
            num = int(parts[i])
            kind = parts[i + 1]
            body = parts[i + 2].strip()
        except (IndexError, ValueError):
            continue
        # body looks like: "What makes up the skeletal system? (bones, the skeleton)"
        # Question = everything up to first "(" answer hint; answer = inside parens.
        q_text, model_a = _split_q_answer(body)
        out.append({
            "num": num,
            "kind": kind,
            "question": q_text,
            "model_answer": model_a,
        })
    return out


# @tag ACADEMY
def _split_q_answer(body: str) -> tuple[str, str]:
    """Separate question text from the parenthetical model answer."""
    # Find first "(" that introduces answer — CKLA convention
    paren_idx = body.find("(")
    if paren_idx < 0:
        return body.strip(), ""
    q = body[:paren_idx].strip().rstrip(":").rstrip()
    # Collect balanced paren content (take first group only)
    depth = 0
    end = paren_idx
    for j, ch in enumerate(body[paren_idx:]):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = paren_idx + j
                break
    answer = body[paren_idx + 1:end].strip()
    # Normalize whitespace
    answer = re.sub(r"\s+", " ", answer)
    q = re.sub(r"\s+", " ", q)
    return q, answer


# @tag ACADEMY
def _extract_word_work(section_text: str) -> str:
    """Find the focus word from the 'Word Work: X' header."""
    m = re.search(r"Word Work:\s*([A-Za-z][A-Za-z\-']*)", section_text)
    return m.group(1).strip().lower() if m else ""


# @tag ACADEMY
def _extract_domain_vocab_index(reader: pypdf.PdfReader) -> dict[int, list[str]]:
    """Parse the Introduction vocabulary index page where all lesson vocab is listed.

    Layout (verbatim from D3 p21):
        Lesson 1
        cells*
        circulate
        functions
        ...
        Lesson 2
        axial bones
        cartilage*
        ...
    Returns {lesson_num: [word, ...]} with asterisk/cross markers stripped.
    """
    idx: dict[int, list[str]] = {}
    # Scan first ~25 pages for the vocab index
    for i in range(min(30, len(reader.pages))):
        text = reader.pages[i].extract_text() or ""
        if "Lesson 1" not in text or "Lesson 2" not in text:
            continue
        # Split by "Lesson N" markers
        parts = re.split(r"\n\s*Lesson\s+(\d+)\s*\n", "\n" + text)
        # parts = [prefix, num1, body1, num2, body2, ...]
        for j in range(1, len(parts), 2):
            try:
                num = int(parts[j])
            except ValueError:
                continue
            body = parts[j + 1] if j + 1 < len(parts) else ""
            # Cut at next "Lesson" or "Comprehension" or two blank lines etc.
            cut = re.search(r"(Comprehension Questions|The following chart|Alignment Chart|Core Content)", body)
            if cut:
                body = body[:cut.start()]
            words: list[str] = []
            for ln in body.split("\n"):
                ls = ln.strip()
                if not ls:
                    continue
                # Remove trailing markers * and +
                ls = re.sub(r"[*+]+\s*$", "", ls).strip()
                # Skip obvious non-vocab (e.g., text descriptions)
                if len(ls) > 40:
                    break  # likely body text, stop this lesson
                if re.search(r"[0-9]", ls):
                    break
                # Vocab entries are 1-3 words, lowercase letters/hyphens/spaces
                if re.match(r"^[A-Za-z][A-Za-z\s\-']+$", ls):
                    words.append(ls.lower())
            if words and num not in idx:
                idx[num] = words
        if idx:
            return idx  # first matching page is enough
    return idx


# @tag ACADEMY
# Canonical CKLA G3 domain titles (file stem → title). Used as override because
# PDF cover extraction produces font-artifact casing (e.g., "Sy STemS and SenSeS").
CKLA_G3_DOMAIN_TITLES: dict[str, str] = {
    "D1_Anth":  "Classic Tales",
    "D2_Anth":  "Classification of Animals",
    "D3_Anth":  "The Human Body: Systems and Senses",
    "D4_Anth":  "Ancient Rome",
    "D5_Anth":  "Light and Sound",
    "D6_Anth":  "The Viking Age",
    "D7_Anth":  "Astronomy",
    "D8_Anth":  "Native Americans: Regions and Cultures",
    "D9_Anth":  "European Exploration of North America",
    "D10_Anth": "Colonial America",
    "D11_Anth": "Ecology",
}


# @tag ACADEMY
def _clean_artifact_casing(s: str) -> str:
    """Fix PDF stylized-heading font artifacts like 'Sy STemS' → 'Systems'.

    Heuristic: merge a short (1–3 char) capitalized token with the next token
    when that next token has internal uppercase (e.g., 'STemS'), then re-title.
    """
    s = re.sub(r"\s+", " ", s).strip()
    # Merge: "Xx YYyy" where second token is 3+ chars with >=2 uppercase in it
    def _merge(m: re.Match) -> str:
        return m.group(1) + m.group(2)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\b([A-Z][a-z]{0,2})\s+([A-Z]{2}[A-Za-z]+)\b", _merge, s)
    # If the result is still mixed-caps inside words (e.g., "SenSeS"), title-case
    def _retitle(m: re.Match) -> str:
        w = m.group(0)
        # Keep words already sanely cased
        if re.match(r"^[A-Z][a-z]+$|^[a-z]+$|^[A-Z]+$", w):
            return w
        return w[0].upper() + w[1:].lower()
    s = re.sub(r"[A-Za-z]+", _retitle, s)
    return s


# @tag ACADEMY
def _extract_domain_title(reader: pypdf.PdfReader, pdf_path: Path | None = None) -> str:
    """Get domain title from page 1, with filename-based canonical override."""
    if pdf_path is not None:
        stem = pdf_path.stem
        if stem in CKLA_G3_DOMAIN_TITLES:
            return CKLA_G3_DOMAIN_TITLES[stem]
    t = reader.pages[0].extract_text() or ""
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    out: list[str] = []
    for ln in lines:
        if "Tell It Again" in ln or "Read-Aloud" in ln or "Grade 3" in ln:
            break
        out.append(ln)
    return _clean_artifact_casing(" ".join(out))


# @tag ACADEMY
def parse_domain(pdf_path: str | Path) -> dict:
    """Parse one CKLA G3 Anthology PDF → structured dict."""
    pdf_path = Path(pdf_path)
    reader = pypdf.PdfReader(str(pdf_path))

    domain_title = _extract_domain_title(reader, pdf_path)
    vocab_index = _extract_domain_vocab_index(reader)
    sections = _collect_lesson_sections(reader)

    lesson_nums = sorted({num for (num, part) in sections})
    lessons: list[dict] = []
    for num in lesson_nums:
        a_pages = sections.get((num, "A"), [])
        if not a_pages:
            continue
        title = _lesson_title(reader, a_pages)
        raw = _join_pages(reader, a_pages)
        stripped = _strip_page_headers(raw, domain_title)
        passage = _extract_passage(stripped, title)
        questions = _extract_questions(stripped)
        word_work = _extract_word_work(stripped)
        lessons.append({
            "lesson_num": num,
            "lesson_title": title,
            "vocabulary": vocab_index.get(num, []),
            "passage": passage,
            "questions": questions,
            "word_work_word": word_work,
            "_page_range_A": [min(a_pages) + 1, max(a_pages) + 1],
        })

    return {
        "source_pdf": pdf_path.name,
        "domain_title": domain_title,
        "lesson_count": len(lessons),
        "lessons": lessons,
    }


if __name__ == "__main__":
    import json
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ckla_g3/D3_Anth.pdf"
    data = parse_domain(path)
    print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])
    print(f"\n... {data['lesson_count']} lessons total")
