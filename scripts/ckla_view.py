"""
scripts/ckla_view.py — Pretty-print one CKLA lesson for review.
Section: Academy
Dependencies: data/academy/ckla_g3/D{N}.json
API: none (CLI tool)

Usage:
    python3 scripts/ckla_view.py 3           # list all lessons in D3
    python3 scripts/ckla_view.py 3 1         # show D3 Lesson 1 in full
    python3 scripts/ckla_view.py 3 1 -p      # passage only
    python3 scripts/ckla_view.py 3 1 -q      # questions only
    python3 scripts/ckla_view.py 3 1 -v      # vocab only
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "academy" / "ckla_g3"

# ANSI colors for readability (disabled automatically when piped)
USE_COLOR = sys.stdout.isatty()


def c(code: str, text: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


BOLD = lambda s: c("1", s)
DIM = lambda s: c("2", s)
CYAN = lambda s: c("36", s)
YELLOW = lambda s: c("33", s)
GREEN = lambda s: c("32", s)
MAGENTA = lambda s: c("35", s)
RED = lambda s: c("31", s)


# @tag ACADEMY
def load_domain(n: int) -> dict:
    path = DATA_DIR / f"D{n}.json"
    if not path.exists():
        print(f"Not found: {path}")
        sys.exit(1)
    return json.loads(path.read_text())


# @tag ACADEMY
def list_lessons(n: int) -> None:
    d = load_domain(n)
    print()
    print(BOLD(f"D{n} — {d['domain_title']}"))
    print(DIM(f"   ({d['lesson_count']} lessons, source: {d['source_pdf']})"))
    print()
    print(f"  {'Lsn':>3}  {'Title':<48}  {'Vocab':>5}  {'Qs':>3}  {'WW':<18}  {'Pass':>5}")
    print(f"  {'-'*3:>3}  {'-'*48:<48}  {'-'*5:>5}  {'-'*3:>3}  {'-'*18:<18}  {'-'*5:>5}")
    for l in d["lessons"]:
        print(
            f"  {l['lesson_num']:>3}  "
            f"{l['lesson_title'][:48]:<48}  "
            f"{len(l['vocabulary']):>5}  "
            f"{len(l['questions']):>3}  "
            f"{(l.get('word_work_word') or '-')[:18]:<18}  "
            f"{len(l['passage']):>5}"
        )
    print()
    print(DIM(f"  Run: python3 scripts/ckla_view.py {n} <lesson_num>  to see full lesson"))
    print()


# @tag ACADEMY
def show_lesson(n: int, lesson_num: int, *, show_passage=True, show_vocab=True, show_q=True) -> None:
    d = load_domain(n)
    lesson = next((l for l in d["lessons"] if l["lesson_num"] == lesson_num), None)
    if not lesson:
        print(f"Lesson {lesson_num} not found in D{n}")
        sys.exit(1)

    print()
    print(BOLD(CYAN(f"╔══ D{n} — {d['domain_title']}")))
    print(BOLD(CYAN(f"║   Lesson {lesson['lesson_num']}: {lesson['lesson_title']}")))
    ww = lesson.get("word_work_word") or "-"
    print(BOLD(CYAN(f"║   Word Work focus: {MAGENTA(ww)}")))
    print(BOLD(CYAN(f"╚════════════════════════════════════════════════════")))
    print()

    if show_vocab:
        print(BOLD(YELLOW(f"▸ Vocabulary ({len(lesson['vocabulary'])} words)")))
        for w in lesson["vocabulary"]:
            marker = " ★" if w == (lesson.get("word_work_word") or "") else ""
            print(f"   • {w}{marker}")
        print()

    if show_passage:
        print(BOLD(GREEN(f"▸ Read-Aloud Passage ({len(lesson['passage'])} chars)")))
        print()
        # Wrap each paragraph (split by single newlines as they come from PDF)
        for para in lesson["passage"].split("\n"):
            para = para.strip()
            if not para:
                continue
            wrapped = textwrap.fill(para, width=84, initial_indent="   ", subsequent_indent="   ")
            print(wrapped)
        print()

    if show_q:
        print(BOLD(MAGENTA(f"▸ Comprehension Questions ({len(lesson['questions'])})")))
        print()
        kind_color = {"Literal": GREEN, "Inferential": YELLOW, "Evaluative": RED}
        for q in lesson["questions"]:
            kc = kind_color.get(q["kind"], lambda s: s)
            header = f"   {BOLD(str(q['num']) + '.')} {kc(q['kind'])}"
            print(header)
            q_wrapped = textwrap.fill(q["question"], width=84, initial_indent="      Q: ", subsequent_indent="         ")
            print(q_wrapped)
            if q["model_answer"]:
                a_wrapped = textwrap.fill(
                    q["model_answer"], width=84,
                    initial_indent="      " + DIM("A: "),
                    subsequent_indent="         ",
                )
                print(a_wrapped)
            print()


# @tag ACADEMY
def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable domains:")
        for i in range(1, 12):
            p = DATA_DIR / f"D{i}.json"
            if p.exists():
                d = json.loads(p.read_text())
                print(f"  D{i:<2}  {d['domain_title']}  ({d['lesson_count']} lessons)")
        return

    try:
        domain_n = int(sys.argv[1])
    except ValueError:
        print(f"Invalid domain number: {sys.argv[1]}")
        sys.exit(1)

    if len(sys.argv) == 2:
        list_lessons(domain_n)
        return

    try:
        lesson_n = int(sys.argv[2])
    except ValueError:
        print(f"Invalid lesson number: {sys.argv[2]}")
        sys.exit(1)

    flags = set(sys.argv[3:])
    any_flag = bool(flags & {"-p", "-q", "-v"})
    show_lesson(
        domain_n, lesson_n,
        show_passage=(not any_flag) or ("-p" in flags),
        show_q=(not any_flag) or ("-q" in flags),
        show_vocab=(not any_flag) or ("-v" in flags),
    )


if __name__ == "__main__":
    main()
