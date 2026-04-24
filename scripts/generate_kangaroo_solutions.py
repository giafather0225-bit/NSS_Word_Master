#!/usr/bin/env python3
"""
generate_kangaroo_solutions.py
==============================
Math Kangaroo past-paper 해설 일괄 생성기

사용법:
  python3 scripts/generate_kangaroo_solutions.py --api-key YOUR_GEMINI_KEY
  python3 scripts/generate_kangaroo_solutions.py --api-key YOUR_KEY --set-id usa_2023_gr56
  python3 scripts/generate_kangaroo_solutions.py --api-key YOUR_KEY --dry-run

원리:
  1. PDF → 페이지 이미지 변환
  2. Gemini Vision에 이미지 + "정답은 X번이야, 왜 X인지 설명해줘" 전달
  3. 모든 문제 해설을 JSON에 저장 (solutions: {"1": "...", "2": "..."})

요구사항:
  pip install pdf2image pillow google-genai
  macOS: brew install poppler
"""

import argparse, json, os, sys, time, glob, base64, re
from pathlib import Path
from io import BytesIO

# ── 경로 ─────────────────────────────────────────────────────
PROJECT = Path(__file__).parent.parent
DATA_DIR = PROJECT / "backend" / "data" / "math" / "kangaroo"
PDF_DIR  = PROJECT / "frontend" / "static" / "math" / "kangaroo" / "pdf"

# ── 프롬프트 ──────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Math Kangaroo competition tutor explaining solutions to students aged 9-14.
For each problem, the CORRECT ANSWER is already given — your job is to explain WHY it's correct.

Rules:
- Be clear and concise (2-5 sentences per problem)
- Show the key step or insight that leads to the answer
- Use simple language appropriate for the grade level
- Do NOT re-state the answer letter at the end — just explain the reasoning
- Return ONLY valid JSON, no markdown fences
"""

def build_prompt(questions_on_page: list[tuple[int, str]], level: str) -> str:
    """questions_on_page: [(q_num, correct_letter), ...]"""
    q_lines = "\n".join(
        f"  Q{num}: correct answer is ({letter})"
        for num, letter in questions_on_page
    )
    return f"""This is page from a Math Kangaroo {level} exam (grade 5-8 level).

The correct answers for the visible questions are:
{q_lines}

For each question listed above, explain step-by-step WHY the given answer is correct.
Respond ONLY with a JSON object like:
{{
  "1": "explanation for Q1...",
  "2": "explanation for Q2...",
  ...
}}"""


def pdf_to_images(pdf_path: Path, dpi: int = 150):
    """Convert PDF pages to PIL images."""
    from pdf2image import convert_from_path
    return convert_from_path(str(pdf_path), dpi=dpi)


def image_to_b64(img) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def call_gemini(client, images_b64: list[str], prompt: str) -> dict:
    """Call Gemini Vision with page images + prompt. Returns {q_num_str: solution}."""
    from google.genai import types

    parts = []
    for b64 in images_b64:
        parts.append(types.Part.from_bytes(
            data=base64.b64decode(b64),
            mime_type="image/png"
        ))
    parts.append(types.Part.from_text(text=prompt))

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=4096,
        )
    )

    text = response.text.strip()
    # strip possible markdown fences
    text = re.sub(r'^```[a-z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


def questions_per_page(total_q: int, n_pages: int) -> list[list[int]]:
    """Evenly distribute question numbers across pages."""
    per_page = total_q // n_pages
    remainder = total_q % n_pages
    pages, q = [], 1
    for i in range(n_pages):
        count = per_page + (1 if i < remainder else 0)
        pages.append(list(range(q, q + count)))
        q += count
    return pages


def process_set(set_id: str, client, dry_run: bool = False, force: bool = False) -> bool:
    json_path = DATA_DIR / f"{set_id}.json"
    if not json_path.exists():
        print(f"  ❌ JSON not found: {json_path}")
        return False

    with open(json_path) as f:
        data = json.load(f)

    # skip if already done (unless force)
    existing = data.get("solutions", {})
    total_q = data.get("total_questions", 30)
    if not force and len(existing) >= total_q:
        print(f"  ⏭  already done ({len(existing)}/{total_q}), skipping")
        return True

    answers = data.get("answers", {})
    if not answers:
        print(f"  ❌ No answers in JSON")
        return False

    pdf_file = data.get("pdf_file", "")
    # resolve path: /static/math/kangaroo/pdf/xxx.pdf
    rel = pdf_file.lstrip("/")
    if rel.startswith("static/"):
        rel = rel[len("static/"):]
    pdf_path = PDF_DIR / Path(rel).name
    if not pdf_path.exists():
        print(f"  ❌ PDF not found: {pdf_path}")
        return False

    print(f"  📄 {set_id}  ({total_q}q, {len(answers)} answers)")

    if dry_run:
        print(f"  [DRY RUN] would process {pdf_path.name}")
        return True

    # convert PDF to images
    try:
        images = pdf_to_images(pdf_path)
    except Exception as e:
        print(f"  ❌ PDF conversion failed: {e}")
        return False

    n_pages = len(images)
    # cover page often page 1 — detect if first page has no questions
    # simple heuristic: use all pages
    page_q_map = questions_per_page(total_q, n_pages)

    solutions = dict(existing)  # start from existing

    for page_idx, q_nums in enumerate(page_q_map):
        # filter to questions that need solutions
        needed = [(q, answers[str(q)]) for q in q_nums
                  if str(q) in answers and str(q) not in solutions]
        if not needed:
            continue

        level = data.get("level_label", data.get("level", "Benjamin"))
        prompt = build_prompt(needed, level)
        b64 = image_to_b64(images[page_idx])

        for attempt in range(3):
            try:
                result = call_gemini(client, [b64], prompt)
                # merge results (keys may come back as ints or strings)
                for k, v in result.items():
                    solutions[str(k)] = str(v)
                print(f"    ✅ page {page_idx+1}: Q{needed[0][0]}-Q{needed[-1][0]} done")
                break
            except json.JSONDecodeError as e:
                print(f"    ⚠️  JSON parse error (attempt {attempt+1}): {e}")
                if attempt == 2:
                    print(f"    ❌ giving up on page {page_idx+1}")
            except Exception as e:
                print(f"    ⚠️  API error (attempt {attempt+1}): {e}")
                if attempt == 2:
                    print(f"    ❌ giving up on page {page_idx+1}")
                time.sleep(2 ** attempt)

        time.sleep(1)  # rate limiting

    if solutions:
        data["solutions"] = {str(k): v for k, v in
                             sorted(solutions.items(), key=lambda x: int(x[0]))}
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  💾 saved {len(solutions)}/{total_q} solutions → {json_path.name}")
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Generate Math Kangaroo solutions via Gemini")
    parser.add_argument("--api-key", required=True, help="Gemini API key")
    parser.add_argument("--set-id", help="Process single set (e.g. intl_2023_benjamin)")
    parser.add_argument("--level", choices=["ecolier","benjamin","cadet","pre_ecolier"],
                        help="Filter by level name")
    parser.add_argument("--year-from", type=int, default=2009, help="Start year (default 2009)")
    parser.add_argument("--year-to",   type=int, default=2025, help="End year (default 2025)")
    parser.add_argument("--dry-run",   action="store_true", help="Preview without API calls")
    parser.add_argument("--force",     action="store_true", help="Regenerate even if solutions exist")
    args = parser.parse_args()

    # init Gemini client
    import google.genai as genai
    client = genai.Client(api_key=args.api_key)

    if args.set_id:
        sets = [args.set_id]
    else:
        # find all past-paper JSONs with PDFs available (intl_ prefix)
        pattern = str(DATA_DIR / "*.json")
        sets = []
        for p in sorted(glob.glob(pattern)):
            with open(p) as f:
                d = json.load(f)
            if d.get("source_type") != "official_past_paper":
                continue
            year = d.get("source_year", 0)
            if not (args.year_from <= year <= args.year_to):
                continue
            # check PDF exists
            pdf_file = d.get("pdf_file","")
            pdf_name = Path(pdf_file).name
            if not (PDF_DIR / pdf_name).exists():
                continue
            set_id = d["set_id"]
            if args.level and d.get("level", "") != args.level:
                continue
            sets.append(set_id)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processing {len(sets)} sets\n")

    ok = fail = skip = 0
    for i, set_id in enumerate(sets, 1):
        print(f"[{i}/{len(sets)}] {set_id}")
        try:
            result = process_set(set_id, client, dry_run=args.dry_run, force=args.force)
            if result:
                ok += 1
            else:
                fail += 1
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            fail += 1

    print(f"\n{'='*50}")
    print(f"Done: {ok} ok, {fail} failed, {skip} skipped")


if __name__ == "__main__":
    main()
