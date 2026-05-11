"""
G3 단원별 리뷰 HTML 생성기.
- 단원당 HTML 1개 (docs/review/G3_U{n}_{slug}.html)
- 인덱스 페이지 1개 (docs/review/index.html)
- 각 항목: stage, id, CCSS, difficulty, 질문, 선택지(정답 강조), expected_errors, hints, solution_steps
- 다크모드 친화 (모바일 가독성)
- "Mark issue" 빠른 메모 영역 (localStorage)
"""
from __future__ import annotations
import json
import html
from pathlib import Path

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
OUT = Path('/Users/markjhlee/NSS_Word_Master/docs/review')
OUT.mkdir(parents=True, exist_ok=True)

STAGES = [
    ('pretest', 'PT', '🎯 사전평가'),
    ('learn', 'LEARN', '📖 개념 학습'),
    ('try', 'TRY', '🔧 시도'),
    ('practice_r1', 'R1', '💪 연습 R1'),
    ('practice_r2', 'R2', '🏃 연습 R2'),
    ('practice_r3', 'R3', '🏆 연습 R3 (워드)'),
]

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system,'Pretendard',sans-serif; margin:0; background:#131722; color:#D1D4DC; line-height:1.55; }
.wrap { max-width: 880px; margin: 0 auto; padding: 16px; }
h1 { color:#E8736A; margin: 4px 0 4px; font-size: 1.4rem; }
h2 { color:#E8736A; margin-top: 32px; padding-top: 16px; border-top: 1px solid #2A2E39; font-size: 1.1rem; }
h3 { color:#D1D4DC; margin: 12px 0 6px; font-size: 0.98rem; }
.meta { color:#787B86; font-size: 0.85rem; }
.stage { background:#1E2329; border-left: 3px solid #E8736A; padding: 10px 14px; margin: 18px 0 10px; font-weight: 600; }
.item { background:#1E2329; border: 1px solid #2A2E39; border-radius: 8px; padding: 14px 16px; margin: 10px 0; }
.item-head { display:flex; gap:8px; flex-wrap:wrap; font-size:0.78rem; color:#787B86; margin-bottom:6px; }
.tag { background:#2A2E39; padding:2px 8px; border-radius:4px; }
.tag.diff-1 { color:#7BC97B; }
.tag.diff-2 { color:#F0C674; }
.tag.diff-3 { color:#EF5350; }
.q { font-size:1.02rem; margin: 8px 0 10px; white-space: pre-wrap; }
.choices { list-style:none; padding:0; margin: 8px 0; }
.choices li { padding: 6px 10px; margin: 4px 0; background:#131722; border:1px solid #2A2E39; border-radius:6px; }
.choices li.correct { background:#1f3a23; border-color:#7BC97B; color:#bef0c6; }
.errors { margin-top: 10px; }
.err { background:#131722; padding: 6px 10px; margin: 4px 0; border-radius:6px; font-size:0.85rem; color:#a8acb8; }
.err .et { color:#E8736A; font-weight:600; margin-right:6px; }
.hint { color:#787B86; font-size:0.85rem; font-style: italic; margin-top: 6px; }
.solution { color:#7BC97B; font-size:0.85rem; margin-top: 6px; }
.solution li { margin-left: 16px; }
.learn-card { background:#1a2f3d; border-left: 3px solid #4a9eff; padding: 10px 14px; margin: 8px 0; }
.flag { float:right; cursor:pointer; padding: 2px 8px; border-radius:4px; background:#2A2E39; font-size:0.75rem; user-select:none; }
.flag.on { background:#E8736A; color:#fff; }
.notes { width:100%; background:#131722; color:#D1D4DC; border:1px solid #2A2E39; border-radius:4px; padding:6px; margin-top:6px; font-family:inherit; font-size:0.85rem; }
.toc { background:#1E2329; padding: 10px 14px; border-radius: 8px; }
.toc a { color:#D1D4DC; display:block; padding: 4px 0; text-decoration:none; }
.toc a:hover { color:#E8736A; }
.nav { position: sticky; top: 0; background:#131722; padding: 8px 0; border-bottom: 1px solid #2A2E39; z-index: 10; }
.nav a { color:#787B86; margin-right: 12px; font-size:0.85rem; text-decoration:none; }
.nav a:hover { color:#E8736A; }
.summary { color:#787B86; font-size:0.85rem; margin-bottom: 8px; }
.export-btn { background:#E8736A; color:#fff; border:none; padding: 6px 12px; border-radius:6px; cursor:pointer; font-size:0.85rem; }
"""

JS = """
const KEY = 'review_flags_' + location.pathname.split('/').pop();
function loadFlags(){ try { return JSON.parse(localStorage.getItem(KEY)||'{}'); } catch(e){ return {}; } }
function saveFlags(f){ localStorage.setItem(KEY, JSON.stringify(f)); }
function toggleFlag(id){
  const f = loadFlags();
  f[id] = f[id] ? null : { ts: Date.now() };
  if (!f[id]) delete f[id];
  saveFlags(f); render();
}
function setNote(id, txt){
  const f = loadFlags();
  if (txt.trim()) { f[id] = f[id] || { ts: Date.now() }; f[id].note = txt; }
  else if (f[id]) { delete f[id].note; if (Object.keys(f[id]).length===1 && 'ts' in f[id]) {} }
  saveFlags(f);
}
function render(){
  const f = loadFlags();
  document.querySelectorAll('.item').forEach(el => {
    const id = el.dataset.id;
    const flag = el.querySelector('.flag');
    if (f[id]) flag.classList.add('on'); else flag.classList.remove('on');
    flag.textContent = f[id] ? '🚩 flagged' : '🚩 mark';
    const ta = el.querySelector('.notes');
    if (ta && f[id] && f[id].note) ta.value = f[id].note;
  });
  const n = Object.keys(f).length;
  const cnt = document.getElementById('flag-count');
  if (cnt) cnt.textContent = n ? `(${n} flagged)` : '';
}
function exportFlags(){
  const f = loadFlags();
  const txt = Object.entries(f).map(([id,v]) => `${id}\\t${v.note||''}`).join('\\n');
  const blob = new Blob([`# Flagged items (${location.pathname.split('/').pop()})\\n${txt}\\n`], {type:'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = location.pathname.split('/').pop().replace('.html','') + '_flags.txt';
  a.click();
}
document.addEventListener('DOMContentLoaded', render);
"""


def esc(x):
    if x is None:
        return ''
    return html.escape(str(x))


def render_item(item: dict, stage_code: str) -> str:
    iid = esc(item.get('id', ''))
    full_id = f"{stage_code}:{iid}"
    head_tags = [
        f'<span class="tag">{stage_code}</span>',
        f'<span class="tag">{esc(item.get("id",""))}</span>',
    ]
    ccss = item.get('ccss')
    if ccss:
        head_tags.append(f'<span class="tag">{esc(ccss)}</span>')
    cpa = item.get('cpa_phase') or item.get('cpa_stage')
    if cpa:
        head_tags.append(f'<span class="tag">{esc(cpa)}</span>')
    diff = item.get('difficulty')
    if diff is not None:
        head_tags.append(f'<span class="tag diff-{esc(diff)}">난이도 {esc(diff)}</span>')
    skill = item.get('skill_tag')
    if skill:
        head_tags.append(f'<span class="tag">{esc(skill)}</span>')

    parts = [f'<div class="item" data-id="{esc(full_id)}">']
    parts.append(f'<span class="flag" onclick="toggleFlag(\'{esc(full_id)}\')">🚩 mark</span>')
    parts.append(f'<div class="item-head">{"".join(head_tags)}</div>')

    # LEARN 카드
    if stage_code == 'LEARN':
        title = esc(item.get('title', ''))
        content = esc(item.get('content', ''))
        parts.append(f'<div class="learn-card"><b>{title}</b><div class="q">{content}</div></div>')
    else:
        q = esc(item.get('question', ''))
        parts.append(f'<div class="q">{q}</div>')
        # 선택지
        choices = item.get('choices') or []
        correct = item.get('correct_answer', '')
        if choices:
            parts.append('<ul class="choices">')
            for c in choices:
                cs = esc(c)
                # 정답 매칭: "B) 588" 또는 "B" 또는 전체 문자열
                is_correct = False
                if correct:
                    if cs.startswith(f'{correct})') or cs.startswith(f'{correct} '):
                        is_correct = True
                    elif cs == esc(correct):
                        is_correct = True
                cls = ' class="correct"' if is_correct else ''
                marker = ' ✓' if is_correct else ''
                parts.append(f'<li{cls}>{cs}{marker}</li>')
            parts.append('</ul>')
        elif correct:
            parts.append(f'<div class="solution">정답: {esc(correct)}</div>')

        # expected_errors
        ee = item.get('expected_errors')
        if isinstance(ee, dict) and ee:
            parts.append('<div class="errors"><b style="font-size:0.85rem;color:#787B86;">예상 함정</b>')
            for ch, info in ee.items():
                if isinstance(info, dict):
                    et = esc(info.get('error_type', ''))
                    note = esc(info.get('note', ''))
                    mid = info.get('misconception_id')
                    mid_str = f' <span class="tag">{esc(mid)}</span>' if mid else ''
                    parts.append(f'<div class="err"><span class="et">{esc(ch)}: {et}</span>{note}{mid_str}</div>')
            parts.append('</div>')

        # hints
        hints = item.get('hints') or []
        if hints:
            parts.append('<div class="hint">💡 ' + ' / '.join(esc(h) for h in hints) + '</div>')

        # solution_steps
        steps = item.get('solution_steps') or []
        if steps:
            parts.append('<div class="solution"><b style="font-size:0.85rem">풀이</b><ol>')
            for s in steps:
                parts.append(f'<li>{esc(s)}</li>')
            parts.append('</ol></div>')

    # misconception_candidates 표시
    cands = item.get('misconception_candidates') or []
    if cands:
        parts.append(f'<div class="meta" style="margin-top:6px">candidates: {esc(", ".join(cands))}</div>')

    # 메모 박스
    parts.append(f'<textarea class="notes" placeholder="메모…" oninput="setNote(\'{esc(full_id)}\', this.value)"></textarea>')
    parts.append('</div>')
    return ''.join(parts)


def render_lesson(lesson_path: Path) -> str:
    d = json.load(open(lesson_path, encoding='utf-8'))
    title = esc(d.get('title') or lesson_path.stem)
    lesson_id = esc(d.get('lesson_id') or lesson_path.stem)
    ccss = d.get('ccss')
    if isinstance(ccss, list):
        ccss = ', '.join(ccss)
    eq = esc(d.get('essential_question', ''))
    out = [f'<h2 id="{lesson_id}">{title} <span class="meta">— {lesson_id}</span></h2>']
    meta_bits = []
    if ccss: meta_bits.append(f'CCSS: {esc(ccss)}')
    if eq: meta_bits.append(f'질문: {eq}')
    if meta_bits:
        out.append(f'<div class="summary">{" · ".join(meta_bits)}</div>')

    for key, code, label in STAGES:
        items = d.get(key) or []
        if not items: continue
        out.append(f'<div class="stage">{label} ({len(items)}문항)</div>')
        for it in items:
            out.append(render_item(it, code))
    return '\n'.join(out)


def render_unit(unit_dir: Path) -> str:
    unit_name = unit_dir.name
    lesson_files = sorted([p for p in unit_dir.glob('L*.json')])
    unit_test = unit_dir / 'unit_test.json'

    toc_links = [f'<a href="#{f.stem}">{f.stem}</a>' for f in lesson_files]
    if unit_test.exists():
        toc_links.append('<a href="#unit_test">📝 unit_test</a>')

    body = []
    for f in lesson_files:
        body.append(render_lesson(f))
    if unit_test.exists():
        body.append('<h2 id="unit_test">📝 Unit Test</h2>')
        body.append(render_lesson(unit_test))

    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(unit_name)} — G3 리뷰</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<div class="nav">
  <a href="index.html">← 인덱스</a>
  <span id="flag-count" style="color:#E8736A"></span>
  <button class="export-btn" onclick="exportFlags()" style="float:right">📥 flag 내보내기</button>
</div>
<h1>{esc(unit_name)}</h1>
<div class="toc">
<b>레슨 목차</b>
{''.join(toc_links)}
</div>
{''.join(body)}
</div>
<script>{JS}</script>
</body></html>"""
    return page


def build_index(unit_names):
    items = '\n'.join(f'<a href="{u}.html">{u}</a>' for u in unit_names)
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>G3 콘텐츠 리뷰</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<h1>📚 G3 콘텐츠 리뷰</h1>
<div class="summary">단원별 모든 항목을 한 페이지로 — 정답·함정·힌트까지 한눈에. 이상한 거 발견하면 🚩 mark, 메모 적고 📥 내보내기.</div>
<div class="toc">{items}</div>
</div></body></html>"""
    return page


def main():
    unit_dirs = sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name != 'misconceptions'])
    names = []
    for ud in unit_dirs:
        html_page = render_unit(ud)
        out = OUT / f'{ud.name}.html'
        out.write_text(html_page, encoding='utf-8')
        names.append(ud.name)
        print(f'  ✓ {out.name}')
    (OUT / 'index.html').write_text(build_index(names), encoding='utf-8')
    print(f'\n✅ {len(names)} units + index.html → {OUT}')
    print(f'   open: file://{OUT}/index.html')


if __name__ == '__main__':
    main()
