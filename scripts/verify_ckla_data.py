#!/usr/bin/env python3
"""
verify_ckla_data.py — CKLA G3 Data Verification

@tag ACADEMY @tag VALIDATION

Strategy:
  Read-only SQLite + JSON inspection of CKLA G3 dataset. Produces two scores:
    - Authority Score (target 100): source fidelity to CKLA Amplify + MW
    - Kid Fitness Score (target 90): age-appropriateness for a 9-year-old learner
  33 validation items across 5 groups (Source Fidelity, Structure, App Functionality,
  Kid Fitness Count, Kid Fitness Ratio) plus 3 informational items.

Usage:
  python3 scripts/verify_ckla_data.py
  python3 scripts/verify_ckla_data.py --json
  python3 scripts/verify_ckla_data.py --domain 6
"""
import argparse, json, os, re, sqlite3, sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Domain constants ──────────────────────────────────────────────────────────
DOMAIN_DAYS = {1:15, 2:17, 3:16, 4:17, 5:19, 6:12, 7:23, 8:15, 9:16, 10:19, 11:12}
TOTAL_DAYS = 181
assert sum(DOMAIN_DAYS.values()) == TOTAL_DAYS

EXPECTED_DOMAIN_COUNT       = 11
EXPECTED_LESSON_COUNT_RANGE = (100, 110)
EXPECTED_QUESTION_COUNT_RANGE = (800, 850)
EXPECTED_WORD_COUNT         = 684
WORD_DEF_MAX_CHARS          = 100
LESSON_PASSAGE_MIN_CHARS    = 200
LESSON_PASSAGE_MAX_CHARS    = 3000
LESSON_DAYS_RATIO_TOLERANCE = 0.30

KF_THRESHOLD = {"definition": 90, "example": 90, "audio": 90, "short_def": 85}
KF_COVERAGE_WEIGHT  = 0.5
WEIGHT_GROUP_1      = 5
WEIGHT_GROUP_2      = 1
WEIGHT_GROUP_3      = 1
WEIGHT_WARN         = 0.3
WEIGHT_DEF_PER_WORD = 0.15
WEIGHT_DAYS_OFF     = 1.0
ORPHAN_CASCADE_CAP  = 10

KF_WEIGHT = {
    "QUESTION_NO_MODEL_ANSWER":  0.1,
    "LESSON_QA_KIND_INCOMPLETE": 0.3,
    "DOMAIN_EVALUATIVE_MISSING": 0.5,
    "LESSON_PASSAGE_TOO_SHORT":  0.3,
}

WORD_CASE_RE = re.compile(r"^[A-Z]?[a-z]+(-[a-z]+)?$")
REQUIRED_TABLES = [
    "ckla_domains", "ckla_lessons", "ckla_questions",
    "us_academy_words", "ckla_word_lessons",
    "ckla_spelling", "ckla_grammar", "ckla_morphology",
]

# ── Color ─────────────────────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
class C:
    G = "\033[32m" if USE_COLOR else ""
    Y = "\033[33m" if USE_COLOR else ""
    R = "\033[31m" if USE_COLOR else ""
    B = "\033[1m"  if USE_COLOR else ""
    D = "\033[2m"  if USE_COLOR else ""
    X = "\033[0m"  if USE_COLOR else ""

# ── Dataclass ─────────────────────────────────────────────────────────────────
@dataclass
class Issue:
    code: str
    severity: str       # "error" | "warn" | "info"
    group: str          # "1"|"2"|"3"|"KF_COUNT"|"KF_RATIO"|"INFO"
    message: str
    weight: float
    count: int = 1
    samples: list = field(default_factory=list)
    actionable: bool = True
    score_impact: dict = field(default_factory=dict)

# ── DB helpers ────────────────────────────────────────────────────────────────
def resolve_db_path() -> Path:
    e = os.environ.get("NSS_DB_PATH")
    return Path(e).expanduser() if e else Path.home() / "NSS_Learning/database/voca.db"

def open_ro(p: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c

def verify_schema(conn) -> bool:
    have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    miss = [t for t in REQUIRED_TABLES if t not in have]
    if miss:
        print(f"❌ Missing required tables: {', '.join(miss)}", file=sys.stderr)
        return False
    return True

def _q(conn, sql, p=()):
    try:
        return conn.execute(sql, p).fetchall()
    except sqlite3.OperationalError:
        return None

def _skip(code, sev, grp, w=0): return Issue(code, sev, grp, "schema mismatch, skipped", w, actionable=False)
def _samps(rows, keys): return [{k: r[k] for k in keys if k in r.keys()} for r in rows[:5]]
def _cnt(c, sql): return ((_q(c, sql) or [[0]])[0][0]) if c else 0

def _row_issue(conn, code, sev, grp, msg, weight, sql, p=(), keys=(), actionable=True):
    rows = _q(conn, sql, p)
    if rows is None: return _skip(code, sev, grp)
    if rows:
        return Issue(code, sev, grp, msg.format(n=len(rows)), weight,
                     count=len(rows), samples=_samps(rows, keys), actionable=actionable)
    return None

# ── JSON loading ──────────────────────────────────────────────────────────────
def load_json(json_dir: Path, df: Optional[int]) -> Dict[int, Optional[dict]]:
    out = {}
    for d in ([df] if df else range(1, 12)):
        f = json_dir / f"D{d}.json"
        try:
            data = json.loads(f.read_text())
            out[d] = data if ("lessons" in data and "domain_number" in data) else None
        except Exception:
            out[d] = None
    return out

# ── Validation — Section 1 ────────────────────────────────────────────────────
def c1_domain_count(conn) -> Optional[Issue]:
    for sql in ("SELECT COUNT(*) FROM ckla_domains WHERE grade=3 AND is_active=1","SELECT COUNT(*) FROM ckla_domains"):
        r = _q(conn, sql)
        if r is not None:
            return Issue("DOMAIN_COUNT","error","2",f"Active G3 domains: {r[0][0]} (expected 11)",WEIGHT_GROUP_1,actionable=False) if r[0][0]!=EXPECTED_DOMAIN_COUNT else None
    return _skip("DOMAIN_COUNT","error","2",WEIGHT_GROUP_1)

def c2_domain_missing_nums(conn) -> Optional[Issue]:
    for sql in ("SELECT domain_num FROM ckla_domains WHERE grade=3 AND is_active=1",
                "SELECT domain_num FROM ckla_domains"):
        r = _q(conn, sql)
        if r is not None:
            miss = [i for i in range(1,12) if i not in {x[0] for x in r}]
            return Issue("DOMAIN_MISSING_NUMS","error","2",f"Missing domain numbers: {miss}",WEIGHT_GROUP_1,actionable=False) if miss else None
    return _skip("DOMAIN_MISSING_NUMS","error","2",WEIGHT_GROUP_1)

def c3_domain_empty(conn) -> Optional[Issue]:
    return _row_issue(conn,"DOMAIN_EMPTY_FIELD","warn","2","{n} domains with empty title/name",WEIGHT_WARN,
        "SELECT id,domain_num FROM ckla_domains WHERE (title IS NULL OR TRIM(title)='') OR (name IS NULL OR TRIM(name)='')",
        keys=("id","domain_num"))

def c4_lesson_count(conn, df) -> Optional[Issue]:
    sql = "SELECT COUNT(*) FROM ckla_lessons l JOIN ckla_domains d ON l.domain_id=d.id WHERE l.is_active=1 AND d.domain_num=?" if df else "SELECT COUNT(*) FROM ckla_lessons WHERE is_active=1"
    r = _q(conn, sql, (df,) if df else ())
    if r is None: return _skip("LESSON_COUNT_OFF","warn","2")
    n = r[0][0]; lo,hi = EXPECTED_LESSON_COUNT_RANGE
    return Issue("LESSON_COUNT_OFF","warn","2",f"Total active lessons: {n} (expected {lo}-{hi})",WEIGHT_WARN,actionable=False) if not (lo<=n<=hi) else None

def c5_lesson_per_domain(conn) -> Issue:
    r = _q(conn,"SELECT d.domain_num, COUNT(l.id) c FROM ckla_domains d LEFT JOIN ckla_lessons l ON l.domain_id=d.id AND l.is_active=1 GROUP BY d.domain_num ORDER BY d.domain_num")
    msg = ", ".join(f"D{x[0]}:{x[1]}" for x in r) if r else "schema mismatch"
    return Issue("LESSON_PER_DOMAIN","info","INFO",f"Lessons per domain: {msg}",0,actionable=False)

def _lesson_issue(conn, df, code, sev, grp, msg, w, where_extra, keys):
    base = f"SELECT l.lesson_num,d.domain_num FROM ckla_lessons l JOIN ckla_domains d ON l.domain_id=d.id WHERE l.is_active=1 AND {where_extra}"
    r = _q(conn, base + (" AND d.domain_num=?" if df else ""), (df,) if df else ())
    if r is None: return _skip(code, sev, grp)
    return Issue(code,sev,grp,msg.format(n=len(r)),w,count=len(r),samples=_samps(r,keys)) if r else None

def c6_empty_passage(conn, df):
    return _lesson_issue(conn,df,"LESSON_EMPTY_PASSAGE","error","1","{n} lessons with empty passage",WEIGHT_GROUP_1,"(l.passage IS NULL OR TRIM(l.passage)='')",("domain_num","lesson_num"))

def c7_passage_too_long(conn, df):
    return _lesson_issue(conn,df,"LESSON_PASSAGE_TOO_LONG","warn","1",f"{{n}} passages >{LESSON_PASSAGE_MAX_CHARS} chars",WEIGHT_WARN,f"LENGTH(l.passage)>{LESSON_PASSAGE_MAX_CHARS}",("domain_num","lesson_num"))

def c8_no_word_work(conn, df):
    return _lesson_issue(conn,df,"LESSON_NO_WORD_WORK","error","3","{n} lessons missing word_work_word",WEIGHT_GROUP_3,"(l.word_work_word IS NULL OR TRIM(l.word_work_word)='')",("domain_num","lesson_num"))

def c9_lesson_orphan(conn) -> Optional[Issue]:
    r = _q(conn,"SELECT l.id,l.lesson_num,l.domain_id FROM ckla_lessons l WHERE l.is_active=1 AND l.domain_id NOT IN (SELECT id FROM ckla_domains)")
    if r is None: return _skip("LESSON_ORPHAN","error","3")
    if not r: return None
    groups: dict = {}
    for x in r: groups.setdefault(x["domain_id"],[]).append(x)
    pen = sum(min(len(g)*WEIGHT_GROUP_3, ORPHAN_CASCADE_CAP) if len(g)>=5 else len(g)*WEIGHT_GROUP_3 for g in groups.values())
    return Issue("LESSON_ORPHAN","error","3",f"{len(r)} orphaned lessons",pen/max(len(r),1),count=len(r),samples=[{"lesson_num":x["lesson_num"],"domain_id":x["domain_id"]} for x in r[:5]])

def c10_question_count(conn, df) -> Optional[Issue]:
    sql = "SELECT COUNT(*) FROM ckla_questions q JOIN ckla_lessons l ON q.lesson_id=l.id JOIN ckla_domains d ON l.domain_id=d.id WHERE l.is_active=1 AND d.domain_num=?" if df else "SELECT COUNT(*) FROM ckla_questions q JOIN ckla_lessons l ON q.lesson_id=l.id WHERE l.is_active=1"
    r = _q(conn, sql, (df,) if df else ())
    if r is None: return _skip("QUESTION_COUNT_OFF","warn","2")
    n = r[0][0]; lo,hi = EXPECTED_QUESTION_COUNT_RANGE
    return Issue("QUESTION_COUNT_OFF","warn","2",f"Total questions: {n} (expected {lo}-{hi})",WEIGHT_WARN,actionable=False) if not (lo<=n<=hi) else None

def _q_issue(conn, df, code, sev, grp, msg, w, where_extra, actionable=True):
    base = f"SELECT q.id,l.lesson_num,d.domain_num FROM ckla_questions q JOIN ckla_lessons l ON q.lesson_id=l.id JOIN ckla_domains d ON l.domain_id=d.id WHERE l.is_active=1 AND {where_extra}"
    r = _q(conn, base + (" AND d.domain_num=?" if df else ""), (df,) if df else ())
    if r is None: return _skip(code, sev, grp)
    return Issue(code,sev,grp,msg.format(n=len(r)),w,count=len(r),samples=_samps(r,("domain_num","lesson_num")),actionable=actionable) if r else None

def c11_kind_invalid(conn, df):
    return _q_issue(conn,df,"QUESTION_KIND_INVALID","error","3","{n} questions with invalid kind",WEIGHT_GROUP_3,"q.kind NOT IN ('Literal','Inferential','Evaluative')")

def c12_empty_text(conn, df):
    return _q_issue(conn,df,"QUESTION_EMPTY_TEXT","error","1","{n} questions with empty text",WEIGHT_GROUP_1,"(q.question IS NULL OR TRIM(q.question)='')")

def c13_no_model_answer(conn, df):
    return _q_issue(conn,df,"QUESTION_NO_MODEL_ANSWER","warn","KF_COUNT","{n} questions missing model_answer",KF_WEIGHT["QUESTION_NO_MODEL_ANSWER"],"(q.model_answer IS NULL OR TRIM(q.model_answer)='')")

def c14_question_orphan(conn) -> Optional[Issue]:
    return _row_issue(conn,"QUESTION_ORPHAN","error","3","{n} questions referencing missing lessons",WEIGHT_GROUP_3,
        "SELECT q.id,q.lesson_id FROM ckla_questions q WHERE q.lesson_id NOT IN (SELECT id FROM ckla_lessons WHERE is_active=1)",
        keys=("id","lesson_id"))

def c15_word_invalid_domain(conn) -> Optional[Issue]:
    return _row_issue(conn,"WORD_INVALID_DOMAIN","warn","2","{n} words with invalid domain_id",WEIGHT_WARN,
        "SELECT w.word,w.domain_id FROM us_academy_words w WHERE w.grade=3 AND w.id IN (SELECT word_id FROM ckla_word_lessons) AND (w.domain_id IS NULL OR w.domain_id<1 OR w.domain_id>11)",
        keys=("word","domain_id"))

def c16_word_case(conn) -> Optional[Issue]:
    r = _q(conn,"SELECT word FROM us_academy_words WHERE grade=3")
    if r is None: return _skip("WORD_CASE_MIXED","warn","2")
    bad = [x[0] for x in r if not WORD_CASE_RE.match(x[0])]
    return Issue("WORD_CASE_MIXED","warn","2",f"{len(bad)} words with unexpected case",WEIGHT_WARN,count=len(bad),samples=[{"word":w} for w in bad[:5]]) if bad else None

def c17_word_link_coverage(conn) -> Issue:
    t = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3")
    l = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND id IN (SELECT word_id FROM ckla_word_lessons)")
    if t is None or l is None: return _skip("WORD_LINK_COVERAGE","info","INFO")
    pct = (l[0][0]/t[0][0]*100) if t[0][0] else 0
    return Issue("WORD_LINK_COVERAGE","info","INFO",f"CKLA word link coverage: {pct:.1f}% ({l[0][0]}/{t[0][0]})",0,actionable=False)

def c18_json_missing(jdata: Dict) -> List[Issue]:
    return [Issue("JSON_FILE_MISSING","error","1",f"D{d}.json missing or malformed",WEIGHT_GROUP_1,samples=[{"domain":d}])
            for d,v in jdata.items() if v is None]

def c19_json_mismatch(conn, jdata: Dict) -> Optional[Issue]:
    miss = []
    for d,data in jdata.items():
        if data is None: continue
        r = _q(conn,"SELECT COUNT(*) FROM ckla_lessons l JOIN ckla_domains dom ON l.domain_id=dom.id WHERE l.is_active=1 AND dom.domain_num=?",(d,))
        if r is None: return _skip("JSON_DB_MISMATCH","warn","1")
        if abs(len(data["lessons"]) - r[0][0]) >= 2:
            miss.append({"domain":d,"json_lessons":len(data["lessons"]),"db_lessons":r[0][0]})
    return Issue("JSON_DB_MISMATCH","warn","1",f"{len(miss)} domains with JSON/DB lesson count mismatch",WEIGHT_WARN,count=len(miss),samples=miss[:5]) if miss else None

def c20_aux_counts(conn) -> Issue:
    counts = {}
    for t in ("ckla_spelling","ckla_grammar","ckla_morphology"):
        r = _q(conn,f"SELECT COUNT(*) FROM {t}"); counts[t] = r[0][0] if r else "?"
    return Issue("CKLA_AUX_COUNT","info","INFO",f"Auxiliary rows — spelling:{counts['ckla_spelling']} grammar:{counts['ckla_grammar']} morphology:{counts['ckla_morphology']}",0,actionable=False)

def c21_dup_lesson_num(conn, df) -> Optional[Issue]:
    r = _q(conn,"SELECT domain_id,lesson_num,COUNT(*) c FROM ckla_lessons WHERE is_active=1 GROUP BY domain_id,lesson_num HAVING c>1")
    if r is None: return _skip("LESSON_DUPLICATE_NUM","error","3")
    if df:
        dom = _q(conn,"SELECT id FROM ckla_domains WHERE domain_num=?",(df,))
        if dom: r = [x for x in r if x["domain_id"] in {d[0] for d in dom}]
    return Issue("LESSON_DUPLICATE_NUM","error","3",f"{len(r)} duplicate lesson_num entries",WEIGHT_GROUP_3,count=len(r),samples=_samps(r,("domain_id","lesson_num","c"))) if r else None

# ── Validation — Section 2 ────────────────────────────────────────────────────
def c22_vocab_insufficient(conn, df) -> List[Issue]:
    r = _q(conn,"SELECT domain_num,id FROM ckla_domains WHERE grade=3 ORDER BY domain_num")
    if r is None: r = _q(conn,"SELECT domain_num,id FROM ckla_domains ORDER BY domain_num")
    if r is None: return [_skip("DOMAIN_TEST_VOCAB_INSUFFICIENT","error","3")]
    out = []
    for row in r:
        if df and row["domain_num"] != df: continue
        tot = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND domain_id=?",(row["id"],))
        dfn = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND domain_id=? AND definition IS NOT NULL AND TRIM(definition)!=''",(row["id"],))
        t_c = tot[0][0] if tot else 0; d_c = dfn[0][0] if dfn else 0
        if d_c < 5:
            msg = f"D{row['domain_num']}: DOMAIN_VOCAB_TOO_FEW: structural limit, manual fix required" if t_c<5 else f"D{row['domain_num']}: only {d_c} words defined (need ≥5)"
            out.append(Issue("DOMAIN_TEST_VOCAB_INSUFFICIENT","error","3",msg,WEIGHT_GROUP_3,actionable=t_c>=5,samples=[{"domain":row["domain_num"],"defined":d_c,"total":t_c}]))
    return out

def c23_qa_kind_incomplete(conn, df) -> Optional[Issue]:
    base = """SELECT l.lesson_num,d.domain_num,
        SUM(CASE WHEN q.kind='Literal' THEN 1 ELSE 0 END) lit,
        SUM(CASE WHEN q.kind='Inferential' THEN 1 ELSE 0 END) inf,
        SUM(CASE WHEN q.kind='Evaluative' THEN 1 ELSE 0 END) ev
        FROM ckla_lessons l JOIN ckla_domains d ON l.domain_id=d.id
        LEFT JOIN ckla_questions q ON q.lesson_id=l.id WHERE l.is_active=1"""
    r = _q(conn, base + (" AND d.domain_num=? GROUP BY l.id" if df else " GROUP BY l.id"), (df,) if df else ())
    if r is None: return _skip("LESSON_QA_KIND_INCOMPLETE","warn","KF_COUNT")
    bad = [{"domain":x["domain_num"],"lesson":x["lesson_num"]} for x in r
           if sum(1 for v in (x["lit"],x["inf"],x["ev"]) if v>0)<3 or max(x["lit"]or 0,x["inf"]or 0,x["ev"]or 0)>4]
    return Issue("LESSON_QA_KIND_INCOMPLETE","warn","KF_COUNT",f"{len(bad)} lessons with incomplete QA kind coverage",KF_WEIGHT["LESSON_QA_KIND_INCOMPLETE"],count=len(bad),samples=bad[:5]) if bad else None

def c24_evaluative_missing(conn, df) -> Optional[Issue]:
    base = "SELECT d.domain_num FROM ckla_domains d WHERE d.grade=3 AND NOT EXISTS (SELECT 1 FROM ckla_questions q JOIN ckla_lessons l ON q.lesson_id=l.id WHERE l.domain_id=d.id AND l.is_active=1 AND q.kind='Evaluative')"
    r = _q(conn, base + (" AND d.domain_num=?" if df else ""), (df,) if df else ())
    if r is None: return _skip("DOMAIN_EVALUATIVE_MISSING","warn","KF_COUNT")
    doms = [x[0] for x in r]
    return Issue("DOMAIN_EVALUATIVE_MISSING","warn","KF_COUNT",f"{len(doms)} domains missing Evaluative questions",KF_WEIGHT["DOMAIN_EVALUATIVE_MISSING"],count=len(doms),samples=[{"domain":d} for d in doms[:5]]) if doms else None

def c25_word_no_def(conn, df) -> Optional[Issue]:
    base = "SELECT word FROM us_academy_words WHERE grade=3 AND id IN (SELECT word_id FROM ckla_word_lessons) AND (definition IS NULL OR TRIM(definition)='')"
    r = _q(conn, base + (" AND domain_id IN (SELECT id FROM ckla_domains WHERE domain_num=?)" if df else ""), (df,) if df else ())
    if r is None: return _skip("WORD_NO_DEFINITION","error","2")
    return Issue("WORD_NO_DEFINITION","error","2",f"{len(r)} CKLA words missing definition",WEIGHT_DEF_PER_WORD,count=len(r),samples=[{"word":x[0]} for x in r[:5]]) if r else None

def c26_29_word_coverage(conn) -> Tuple[List[Optional[Issue]], Dict]:
    W = "grade=3 AND id IN (SELECT word_id FROM ckla_word_lessons)"
    cov = {"definition":0.0,"example":0.0,"audio":0.0,"short_def":0.0,"short_def_denominator":0}
    tot = _q(conn,f"SELECT COUNT(*) FROM us_academy_words WHERE {W}")
    if tot is None: return [None,None,None], cov
    n = tot[0][0]
    if n == 0: return [None,None,None], cov
    def pct(extra): r=_q(conn,f"SELECT COUNT(*) FROM us_academy_words WHERE {W} AND {extra}"); return r[0][0]/n if r else 0.0
    cov["definition"] = pct("definition IS NOT NULL AND TRIM(definition)!=''")
    cov["example"]    = pct("example_1 IS NOT NULL AND TRIM(example_1)!=''")
    cov["audio"]      = pct("audio_url IS NOT NULL AND TRIM(audio_url)!=''")
    dn = round(cov["definition"]*n); cov["short_def_denominator"] = dn
    if dn:
        r = _q(conn,f"SELECT COUNT(*) FROM us_academy_words WHERE {W} AND definition IS NOT NULL AND TRIM(definition)!='' AND LENGTH(definition)<={WORD_DEF_MAX_CHARS}")
        cov["short_def"] = r[0][0]/dn if r else 0.0
    codes = {"example":"WORD_NO_EXAMPLE","audio":"WORD_NO_AUDIO","short_def":"WORD_DEFINITION_TOO_LONG"}
    issues = []
    for name in ("example","audio","short_def"):
        p = cov[name]*100; th = KF_THRESHOLD[name]
        issues.append(Issue(codes[name],"warn","KF_RATIO",f"Coverage {name}: {p:.1f}% (target {th}%)",0) if p<th else None)
    return issues, cov

def c28_days_ratio(conn, df) -> List[Issue]:
    tot = _q(conn,"SELECT COUNT(*) FROM ckla_lessons WHERE is_active=1")
    if tot is None: return [_skip("LESSON_DAYS_RATIO_OFF","warn","2")]
    tl = tot[0][0]; out = []
    for d in ([df] if df else range(1,12)):
        r = _q(conn,"SELECT COUNT(*) FROM ckla_lessons l JOIN ckla_domains dom ON l.domain_id=dom.id WHERE l.is_active=1 AND dom.domain_num=?",(d,))
        if r is None: break
        act = r[0][0]; exp = round(DOMAIN_DAYS[d]*tl/TOTAL_DAYS) if tl else DOMAIN_DAYS[d]
        if exp>0 and abs(act-exp)/exp > LESSON_DAYS_RATIO_TOLERANCE:
            out.append(Issue("LESSON_DAYS_RATIO_OFF","warn","2",f"D{d}: {act} lessons (expected ~{exp})",WEIGHT_DAYS_OFF,samples=[{"domain":d,"actual":act,"expected":exp}]))
    return out

def c30_passage_short(conn, df):
    return _lesson_issue(conn,df,"LESSON_PASSAGE_TOO_SHORT","warn","KF_COUNT",f"{{n}} passages <{LESSON_PASSAGE_MIN_CHARS} chars",KF_WEIGHT["LESSON_PASSAGE_TOO_SHORT"],f"l.passage IS NOT NULL AND TRIM(l.passage)!='' AND LENGTH(l.passage)<{LESSON_PASSAGE_MIN_CHARS}",("domain_num","lesson_num"))

# ── Validation — Section 3 ────────────────────────────────────────────────────
def _aux_check(conn, code, sev, w, table, value_col, is_error):
    r = _q(conn,f"SELECT unit,{value_col} FROM {table} ORDER BY unit")
    if r is None: return _skip(code,sev,"2",w)
    have = {x["unit"]:x[value_col] for x in r}
    miss = [u for u in range(1,13) if u not in have]
    empty = [u for u,v in have.items() if not v or v=="[]"]
    if miss or empty:
        parts = ([f"missing units: {miss}"] if miss else []) + ([f"units with empty content: {empty}"] if empty else [])
        return Issue(code,sev,"2","; ".join(parts),w,count=len(miss)+len(empty))
    return None

def c32_grammar(conn):    return _aux_check(conn,"CKLA_GRAMMAR_INCOMPLETE","warn",WEIGHT_WARN,"ckla_grammar","topics",False)
def c33_morphology(conn): return _aux_check(conn,"CKLA_MORPHOLOGY_INCOMPLETE","warn",WEIGHT_WARN,"ckla_morphology","topics",False)

def c31_spelling(conn) -> Optional[Issue]:
    r = _q(conn,"SELECT unit,COUNT(DISTINCT week) w FROM ckla_spelling GROUP BY unit")
    if r is None: return _skip("CKLA_SPELLING_INCOMPLETE","error","2",WEIGHT_GROUP_2)
    have = {x["unit"]:x["w"] for x in r}
    miss = [u for u in range(1,13) if u not in have]
    few  = [u for u,w in have.items() if w<3]
    if miss or few:
        parts = ([f"missing units: {miss}"] if miss else []) + ([f"units with <3 weeks: {few}"] if few else [])
        return Issue("CKLA_SPELLING_INCOMPLETE","error","2","; ".join(parts),WEIGHT_GROUP_2,count=len(miss)+len(few))
    return None

# ── Run all checks ────────────────────────────────────────────────────────────
def run_all_checks(conn, jdata, df) -> Tuple[List[Issue], Dict]:
    iss: List[Issue] = []
    def add(*args):
        for a in args:
            if a is None: continue
            iss.extend(a) if isinstance(a, list) else iss.append(a)

    dc = c1_domain_count(conn); add(dc)
    if dc is None or dc.severity != "error": add(c2_domain_missing_nums(conn))
    add(c3_domain_empty(conn), c4_lesson_count(conn,df), c5_lesson_per_domain(conn))
    add(c6_empty_passage(conn,df), c7_passage_too_long(conn,df), c8_no_word_work(conn,df))
    add(c9_lesson_orphan(conn), c10_question_count(conn,df))
    add(c11_kind_invalid(conn,df), c12_empty_text(conn,df), c13_no_model_answer(conn,df))
    add(c14_question_orphan(conn), c15_word_invalid_domain(conn), c16_word_case(conn))
    add(c17_word_link_coverage(conn), c18_json_missing(jdata), c19_json_mismatch(conn,jdata))
    add(c20_aux_counts(conn), c21_dup_lesson_num(conn,df))
    add(c22_vocab_insufficient(conn,df), c23_qa_kind_incomplete(conn,df), c24_evaluative_missing(conn,df))
    add(c25_word_no_def(conn,df))
    cov_issues, cov = c26_29_word_coverage(conn); add(cov_issues)
    add(c28_days_ratio(conn,df), c30_passage_short(conn,df))
    add(c31_spelling(conn), c32_grammar(conn), c33_morphology(conn))
    return iss, cov

# ── Scoring ───────────────────────────────────────────────────────────────────
def calc_scores(issues: List[Issue], cov: Dict) -> Dict:
    auth_pen = sum(i.weight*i.count for i in issues if i.group in ("1","2","3") and i.severity in ("error","warn"))
    kf_cnt   = sum(KF_WEIGHT.get(i.code,0)*i.count for i in issues if i.group=="KF_COUNT")
    kf_rat   = sum(max(0,KF_THRESHOLD[n]-cov.get(n,0)*100)*KF_COVERAGE_WEIGHT
                   for n in ("example","audio","short_def"))
    for i in issues:
        ai = i.weight*i.count if i.group in ("1","2","3") and i.severity in ("error","warn") else 0
        ki = KF_WEIGHT.get(i.code,0)*i.count if i.group=="KF_COUNT" else 0
        i.score_impact = {"authority":round(ai,3),"kid_fitness":round(ki,3)}
    return {"authority":round(max(0.0,100-auth_pen),1),"authority_raw_penalty":round(auth_pen,1),
            "kid_fitness":round(max(0.0,100-kf_cnt-kf_rat),1),"kf_count_penalty":round(kf_cnt,2),"kf_ratio_penalty":round(kf_rat,2)}

def verdict(sc) -> Tuple[str,str]:
    a,k = sc["authority"],sc["kid_fitness"]
    if a>=100 and k>=90:   return "ok","✅ Ready for high-quality learning"
    if a>=100 and k<90:    return "warning","⚠️ Authoritative but needs enrichment"
    if 95<=a<100 and k>=90:return "warning","⚠️ Source data has minor gaps; learning may proceed"
    if a<80:               return "critical","❌ Major data integrity issues"
    return "critical","❌ Significant gaps; address critical issues first"

# ── Remediation ───────────────────────────────────────────────────────────────
def build_remediation(issues, cov, sc) -> List[Dict]:
    items = []
    for i in issues:
        if i.score_impact.get("authority",0)>0 and i.actionable:
            items.append({"category":"authority","code":i.code,"description":i.message,
                          "expected_improvement":round(i.score_impact["authority"],2),"actionable":True,"manual_fix_required":False})
    for i in issues:
        if i.group=="KF_COUNT" and i.actionable and i.code in KF_WEIGHT:
            items.append({"category":"kid_fitness","code":i.code,"description":i.message,
                          "expected_improvement":round(KF_WEIGHT[i.code]*i.count,2),"actionable":True,
                          "manual_fix_required":i.code=="DOMAIN_EVALUATIVE_MISSING"})
    codes = {"example":"WORD_NO_EXAMPLE","audio":"WORD_NO_AUDIO","short_def":"WORD_DEFINITION_TOO_LONG"}
    for name,th in [(n,KF_THRESHOLD[n]) for n in ("example","audio","short_def")]:
        p = cov.get(name,0)*100
        if p<th:
            items.append({"category":"kid_fitness","code":codes[name],"description":f"Improve {name} coverage from {p:.1f}% to {th}%",
                          "expected_improvement":round(max(0,th-p)*KF_COVERAGE_WEIGHT,2),"actionable":True,"manual_fix_required":name=="short_def"})
    a_items = sorted((x for x in items if x["category"]=="authority"),  key=lambda x:-x["expected_improvement"])
    k_items = sorted((x for x in items if x["category"]=="kid_fitness"),key=lambda x:-x["expected_improvement"])
    for rank,item in enumerate(a_items+k_items,1): item["rank"]=rank
    return a_items+k_items

# ── Domain matrix ─────────────────────────────────────────────────────────────
def domain_matrix(conn, df) -> List[Dict]:
    tot = _q(conn,"SELECT COUNT(*) FROM ckla_lessons WHERE is_active=1")
    tl = tot[0][0] if tot else 0
    out = []
    for d in ([df] if df else range(1,12)):
        la = _q(conn,"SELECT COUNT(*) FROM ckla_lessons l JOIN ckla_domains dom ON l.domain_id=dom.id WHERE l.is_active=1 AND dom.domain_num=?",(d,))
        act = la[0][0] if la else 0; exp = round(DOMAIN_DAYS[d]*tl/TOTAL_DAYS) if tl else DOMAIN_DAYS[d]
        wc = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND domain_id IN (SELECT id FROM ckla_domains WHERE domain_num=?)",(d,))
        wn = wc[0][0] if wc else 0
        dc = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND domain_id IN (SELECT id FROM ckla_domains WHERE domain_num=?) AND definition IS NOT NULL AND TRIM(definition)!=''",(d,))
        dp = round(dc[0][0]/wn*100 if dc and wn else 0,1)
        ac = _q(conn,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3 AND domain_id IN (SELECT id FROM ckla_domains WHERE domain_num=?) AND audio_url IS NOT NULL AND TRIM(audio_url)!=''",(d,))
        ap = round(ac[0][0]/wn*100 if ac and wn else 0,1)
        ratio_ok = act==0 or abs(act-exp)/max(exp,1)<=LESSON_DAYS_RATIO_TOLERANCE
        out.append({"domain":d,"lessons_actual":act,"lessons_expected":exp,"words":wn,"definition_pct":dp,"audio_pct":ap,"status":"ok" if ratio_ok and dp>=95 else "warn"})
    return out

# ── Comparison ────────────────────────────────────────────────────────────────
def find_prev(db_path, df) -> Optional[Dict]:
    rep = REPO_ROOT/"reports"
    if not rep.exists(): return None
    for f in sorted(rep.glob("ckla_verify_*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        try:
            d = json.loads(f.read_text())
            if d.get("db_path")==str(db_path) and d.get("sources",{}).get("domain_filter")==df:
                return d
        except Exception: pass
    return None

# ── Console ───────────────────────────────────────────────────────────────────
def render(args, db_path, issues, cov, sc, rem, prev, dm):
    SEP = "═"*63
    run_mode = f"domain {args.domain}" if args.domain else "full"
    print(f"\n{SEP}\n{C.B}CKLA G3 Data Verification{C.X}")
    print(f"Source: CKLA G3 (Amplify) + Merriam-Webster Elementary")
    print(f"DB:     {db_path}\nRun:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({run_mode})\n{SEP}")
    errs = [i for i in issues if i.severity=="error" and i.group in ("1","2","3")]
    if errs:
        print(f"\n{C.R}[Critical Issues]{C.X}")
        for i in errs[:5]: print(f"  🚨 {i.code}: {i.message}")
    a,kf = sc["authority"],sc["kid_fitness"]
    ac = C.G if a>=100 else C.Y if a>=95 else C.R
    print(f"\n{C.B}Authority Score: {ac}{a:.1f}{C.X}{C.B} / 100{C.X} (target: 100)")
    for g,lbl in (("1","Source Fidelity"),("2","Structure"),("3","App Functionality")):
        gi = [i for i in issues if i.group==g and i.severity in ("error","warn")]
        if not gi: print(f"  {C.G}✅{C.X} {lbl}: clean")
        else:
            print(f"  Group {g} ({lbl}):")
            for i in gi[:3]: print(f"    {'🚨' if i.severity=='error' else '⚠️'} {i.code}: {i.message}")
    kc = C.G if kf>=90 else C.Y if kf>=80 else C.R
    ki = "✅" if kf>=90 else "⚠️"
    print(f"\n{C.B}Kid Fitness Score: {kc}{kf:.1f}{C.X}{C.B} / 100{C.X} (target: 90) {ki}")
    print("  Word Data Coverage:")
    for name,lbl in (("definition","Definition"),("example","Example"),("audio","Audio"),("short_def","Short Def")):
        p=cov.get(name,0)*100; th=KF_THRESHOLD[name]
        icon=(C.G+"✅"+C.X) if p>=th else (C.Y+"⚠️"+C.X)
        note=" (Authority-tracked, no KF impact)" if name=="definition" else f" (target {th}%)"
        print(f"    {lbl:12s}: {p:5.1f}% {icon}{note}")
    kf_cnt_iss = [i for i in issues if i.group=="KF_COUNT" and i.count>0]
    if kf_cnt_iss:
        print("  Structural Fitness:")
        for i in kf_cnt_iss: print(f"    {i.message} (-{KF_WEIGHT.get(i.code,0)*i.count:.2f} pts)")
    if dm:
        print(f"\n{C.B}Domain Summary:{C.X}")
        print(f"{'Domain':8} {'Lessons':12} {'Words':6} {'Defined':8} {'Audio':6} Status")
        print("-"*52)
        for row in dm:
            st=(C.G+"✅"+C.X) if row["status"]=="ok" else (C.Y+"⚠️"+C.X)
            print(f"D{row['domain']:<7} {row['lessons_actual']}/{row['lessons_expected']:<10} {row['words']:<6} {row['definition_pct']:5.0f}%   {row['audio_pct']:5.0f}%  {st}")
    _,vm = verdict(sc); print(f"\n{C.B}Verdict: {vm}{C.X}")
    if rem:
        print(f"\n{C.B}Remediation Priorities:{C.X}")
        ar = [r for r in rem if r["category"]=="authority"]
        kr = [r for r in rem if r["category"]=="kid_fitness"]
        if ar:
            print(f"\n  [Authority Score Impact] (current {a:.1f} → target 100)")
            for r in ar: print(f"    {r['rank']}. {r['description']:<48} +{r['expected_improvement']:.2f} pts{' (manual fix required)' if r.get('manual_fix_required') else ''}")
        if kr:
            print(f"\n  [Kid Fitness Score Impact] (current {kf:.1f} → target 90)")
            for r in kr: print(f"    {r['rank']}. {r['description']:<48} +{r['expected_improvement']:.2f} pts{' (manual fix required)' if r.get('manual_fix_required') else ''}")
    if prev:
        pa=prev.get("scores",{}).get("authority",{}).get("value",0); pk=prev.get("scores",{}).get("kid_fitness",{}).get("value",0)
        print(f"\nCompared to previous run ({prev.get('ran_at','')[:19]}):\n  Authority: {a:.1f} ({a-pa:+.1f})  Kid Fitness: {kf:.1f} ({kf-pk:+.1f})")
    else:
        print("\nNo comparable previous run found.")
    print(SEP+"\n")

# ── JSON report ───────────────────────────────────────────────────────────────
def save_json(args, db_path, conn2, issues, cov, sc, rem, prev, dm) -> Path:
    rep = REPO_ROOT/"reports"; rep.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = rep/f"ckla_verify_{ts}.json"
    vs,vm = verdict(sc)
    report = {
        "version":"1.0","ran_at":datetime.now().isoformat(),"db_path":str(db_path),
        "sources":{"db":str(db_path),"json_dir":"data/academy/ckla_g3","json_files":[f"D{d}.json" for d in ([args.domain] if args.domain else range(1,12))],"domain_filter":args.domain},
        "summary":{"domains":EXPECTED_DOMAIN_COUNT,"lessons":_cnt(conn2,"SELECT COUNT(*) FROM ckla_lessons WHERE is_active=1"),"questions":_cnt(conn2,"SELECT COUNT(*) FROM ckla_questions q JOIN ckla_lessons l ON q.lesson_id=l.id WHERE l.is_active=1"),"words":_cnt(conn2,"SELECT COUNT(*) FROM us_academy_words WHERE grade=3"),"spelling_rows":_cnt(conn2,"SELECT COUNT(*) FROM ckla_spelling"),"grammar_rows":_cnt(conn2,"SELECT COUNT(*) FROM ckla_grammar"),"morphology_rows":_cnt(conn2,"SELECT COUNT(*) FROM ckla_morphology")},
        "scores":{"authority":{"value":sc["authority"],"target":100,"raw_penalty":sc["authority_raw_penalty"],"status":"ok" if sc["authority"]>=100 else "below_target"},"kid_fitness":{"value":sc["kid_fitness"],"target":90,"status":"ok" if sc["kid_fitness"]>=90 else "below_target"}},
        "verdict":{"status":vs,"message":vm.lstrip("✅⚠️❌ ")},
        "word_coverage":{"definition":round(cov.get("definition",0),3),"example":round(cov.get("example",0),3),"audio":round(cov.get("audio",0),3),"short_def":round(cov.get("short_def",0),3),"short_def_denominator":cov.get("short_def_denominator",0)},
        "issues":[{"code":i.code,"severity":i.severity,"group":i.group,"message":i.message,"weight":i.weight,"count":i.count,"actionable":i.actionable,"score_impact":i.score_impact,"samples":i.samples,"samples_total":len(i.samples)} for i in issues],
        "domain_matrix":dm,"remediation":rem,
        "previous_run_comparison":{"compared_to":prev.get("ran_at",""),"authority_delta":round(sc["authority"]-prev.get("scores",{}).get("authority",{}).get("value",0),1),"kid_fitness_delta":round(sc["kid_fitness"]-prev.get("scores",{}).get("kid_fitness",{}).get("value",0),1)} if prev else None,
    }
    path.write_text(json.dumps(report,indent=2,default=str))
    return path

# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="CKLA G3 Data Verification — Authority + Kid Fitness scores",
        epilog="Examples:\n  python3 scripts/verify_ckla_data.py\n  python3 scripts/verify_ckla_data.py --json\n  python3 scripts/verify_ckla_data.py --domain 6\n\nNSS_DB_PATH env var overrides default DB path. Reports saved to: <repo_root>/reports/",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json",action="store_true",help="Save JSON report to reports/")
    p.add_argument("--domain",type=int,metavar="N",help="Validate single domain (1-11)")
    return p

def main() -> int:
    args = parse_args().parse_args()
    if args.domain is not None and not (1<=args.domain<=11):
        print(f"❌ --domain must be between 1 and 11 (got {args.domain})",file=sys.stderr); return 1
    db = resolve_db_path()
    if not db.is_file():
        print(f"❌ DB file not found or not a regular file: {db}",file=sys.stderr); return 2
    conn = open_ro(db)
    if not verify_schema(conn):
        conn.close(); return 2
    jdata = load_json(REPO_ROOT/"data/academy/ckla_g3",args.domain)
    conn.execute("BEGIN")
    try:
        issues, cov = run_all_checks(conn, jdata, args.domain)
    finally:
        conn.execute("ROLLBACK")
    conn.close()
    sc  = calc_scores(issues, cov)
    rem = build_remediation(issues, cov, sc)
    prev = find_prev(db, args.domain)
    conn2 = open_ro(db)
    try:
        dm = domain_matrix(conn2, args.domain)
        if args.json:
            path = save_json(args, db, conn2, issues, cov, sc, rem, prev, dm)
    except Exception:
        dm = []
        if args.json:
            path = save_json(args, db, None, issues, cov, sc, rem, prev, dm)
    finally:
        conn2.close()
    if args.json:
        print(f"Saved to {path.relative_to(REPO_ROOT)}")
        print(f"Authority: {sc['authority']:.1f}/100  Kid Fitness: {sc['kid_fitness']:.1f}/100")
    else:
        render(args, db, issues, cov, sc, rem, prev, dm)
    return 1 if any(i.severity=="error" for i in issues) else 0

if __name__ == "__main__":
    sys.exit(main())
