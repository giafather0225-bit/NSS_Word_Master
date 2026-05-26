"""
services/report_engine_html.py — Weekly report HTML email builder
Section: Parent
Dependencies: none (standalone template helpers)
API: called by services/report_engine.py (build_html_report)
"""

# ── Email palette (theme.css hex equivalents — CSS vars not allowed in email) ──
_C = {
    "page":         "#FAF6EF",
    "card":         "#FFFFFF",
    "surface":      "#EFE8DB",
    "text":         "#2B2722",
    "text_sub":     "#706659",
    "text_hint":    "#A79A89",
    "text_on":      "#FFFFFF",
    "border":       "#DCD2C2",
    "border_sub":   "#EBE3D5",
    # sections
    "eng":          "#7FA8CC",
    "eng_light":    "#EEF4FA",
    "eng_soft":     "#CFE0EE",
    "eng_ink":      "#345A80",
    "math":         "#8AC4A8",
    "math_light":   "#EEF7F2",
    "math_soft":    "#CFE6D9",
    "math_ink":     "#3A6A54",
    "diary":        "#E09AAE",
    "arcade":       "#EEC770",
    "arcade_light": "#FBF3DE",
    "arcade_ink":   "#7A5A1E",
    "rewards":      "#B8A4DC",
    "rewards_light":"#F2ECFA",
    # state
    "success":      "#8FBF87",
    "success_light":"#E8F5E4",
    "success_ink":  "#4E7A46",
    "error":        "#D97A7A",
    "error_light":  "#FAEAEA",
    "error_ink":    "#8A4538",
    "warning":      "#EEC770",
    "warning_light":"#FBF3DE",
    # brand
    "primary":      "#E09AAE",
}


# ── Private helpers ───────────────────────────────────────────────────────────

def _bar(value: int, max_val: int, color: str, height: int = 40) -> str:
    pct = int(value / max_val * 100) if max_val else 0
    bg  = _C["border_sub"]
    return (
        f'<td style="text-align:center;vertical-align:bottom;padding:0 3px;">' +
        f'<div style="background:{color};width:30px;height:{max(pct * height // 100, 2)}px;' +
        f'border-radius:4px 4px 0 0;margin:0 auto;"></div></td>'
    )


def _acc_row(label: str, acc: float, count: int) -> str:
    color = _C["success"] if acc >= 80 else (_C["warning"] if acc >= 60 else _C["error"])
    w     = int(acc)
    return f"""
    <tr>
      <td style="font-size:12px;color:{_C['text']};width:100px;padding:5px 0;">{label}</td>
      <td style="padding:5px 8px;">
        <div style="background:{_C['border_sub']};border-radius:4px;height:7px;">
          <div style="background:{color};width:{w}%;height:7px;border-radius:4px;"></div>
        </div>
      </td>
      <td style="font-size:12px;font-weight:700;color:{color};width:40px;">{acc}%</td>
      <td style="font-size:11px;color:{_C['text_hint']};padding-left:6px;">{count}x</td>
    </tr>"""


def _ckla_section(ckla: dict, c: dict) -> str:
    """Build CKLA email HTML block. Returns empty string if no data."""
    if not ckla or ckla.get("total_lessons", 0) == 0:
        return ""

    pct     = ckla.get("grade_pct", 0)
    rank    = ckla.get("rank", "Beginner")
    lessons = ckla.get("lessons_this_week", 0)
    total   = ckla.get("total_lessons", 1)
    done    = ckla.get("completed_total", 0)
    days    = ckla.get("days_studied", 0)
    qa_acc  = ckla.get("qa_accuracy")
    weak    = ckla.get("weak_lessons", []) or []

    qa_row = ""
    if qa_acc is not None:
        qa_color = c["success"] if qa_acc >= 80 else (c["warning"] if qa_acc >= 60 else c["error"])
        qa_row = f"""
        <tr>
          <td style="font-size:13px;color:{c['text_sub']};padding:4px 0;">Q&amp;A Accuracy (7d)</td>
          <td style="font-size:13px;font-weight:700;color:{qa_color};text-align:right;">{qa_acc}%</td>
        </tr>"""

    weak_block = ""
    if weak:
        rows = ""
        for w in weak:
            acc = int(w["accuracy"])
            color = c["error"] if acc < 50 else c["warning"]
            rows += f"""
            <tr>
              <td style="font-size:13px;color:{c['text']};padding:4px 0;">{w['title']}</td>
              <td style="font-size:12px;color:{c['text_sub']};padding:4px 12px;">{w['attempts']} Q&amp;A</td>
              <td style="font-size:13px;font-weight:700;color:{color};text-align:right;">{acc}%</td>
            </tr>"""
        weak_block = f"""
        {_section_header("CKLA — Lessons Needing Review", c['error'], c['error_light'], c['error_ink'])}
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
              {rows}
            </table>
          </td>
        </tr>"""

    header = _section_header("CKLA Grade 3", c["eng"], c["eng_light"], c["eng_ink"])
    return f"""
    {header}
    <tr>
      <td>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-size:13px;color:{c['text_sub']};padding:4px 0;">This week</td>
            <td style="font-size:13px;font-weight:700;color:{c['eng_ink']};text-align:right;">{lessons} lesson{'s' if lessons != 1 else ''} · {days} day{'s' if days != 1 else ''}</td>
          </tr>
          <tr>
            <td style="font-size:13px;color:{c['text_sub']};padding:4px 0;">Overall progress</td>
            <td style="font-size:13px;font-weight:700;color:{c['eng_ink']};text-align:right;">{done}/{total} ({pct}%) · {rank}</td>
          </tr>
          {qa_row}
          <tr>
            <td colspan="2" style="padding:6px 0 2px;">
              <div style="background:{c['border_sub']};border-radius:4px;height:6px;">
                <div style="background:{c['eng']};width:{pct}%;height:6px;border-radius:4px;"></div>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    {weak_block}"""


def _section_header(title: str, color: str, light: str, ink: str) -> str:
    return f"""
    <tr>
      <td style="padding:24px 0 12px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="width:4px;background:{color};border-radius:2px;">&nbsp;</td>
            <td style="padding-left:12px;">
              <span style="font-size:11px;font-weight:700;letter-spacing:0.08em;
                color:{ink};text-transform:uppercase;">{title}</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


# ── Public API ────────────────────────────────────────────────────────────────

def build_html_report(data: dict, child_name: str = "Gia") -> str:
    """Build the HTML email template. No emoji; section bars provide color separation."""
    c = _C

    # Daily XP bars
    max_xp  = max((d["xp"] for d in data["daily_activity"]), default=1) or 1
    day_bars = ""
    for d in data["daily_activity"]:
        pct   = int(d["xp"] / max_xp * 100)
        color = c["eng"] if pct > 0 else c["border_sub"]
        h     = max(pct * 48 // 100, 2)
        day_bars += f"""
        <td style="text-align:center;vertical-align:bottom;padding:0 3px;">
          <div style="background:{color};width:30px;height:{h}px;
               border-radius:4px 4px 0 0;margin:0 auto;"></div>
          <div style="font-size:10px;color:{c['text_hint']};margin-top:4px;">{d['label']}</div>
          <div style="font-size:9px;color:{c['text_hint']};margin-top:1px;">{d['xp']}xp</div>
        </td>"""

    # Stage accuracy rows
    stage_rows = "".join(_acc_row(s["label"], s["accuracy"], s["count"]) for s in data["stage_stats"])
    if not stage_rows:
        stage_rows = f'<tr><td colspan="4" style="color:{c["text_hint"]};font-size:13px;padding:8px 0;">No stage data this week.</td></tr>'

    # Weak word rows
    weak_rows = ""
    for w in data["weak_words"]:
        acc   = w["accuracy"]
        color = c["error"] if acc < 50 else c["warning"]
        weak_rows += f"""
        <tr>
          <td style="font-size:13px;font-weight:700;color:{c['text']};padding:5px 0;">{w['word']}</td>
          <td style="font-size:12px;color:{c['text_sub']};padding:5px 12px;">{w['attempts']} attempts</td>
          <td style="font-size:13px;font-weight:700;color:{color};">{int(acc)}%</td>
        </tr>"""
    if not weak_rows:
        weak_rows = f'<tr><td colspan="3" style="font-size:13px;color:{c["success_ink"]};padding:8px 0;">No weak words this week — great work!</td></tr>'

    # Lesson tags
    lesson_tags = ""
    for l in data["lessons_studied"][:6]:
        lesson_tags += (
            f'<span style="display:inline-block;background:{c["eng_light"]};' +
            f'color:{c["eng_ink"]};border-radius:99px;padding:3px 12px;' +
            f'font-size:12px;margin:3px 3px 3px 0;">{l["lesson"]}</span>'
        )
    if not lesson_tags:
        lesson_tags = f'<span style="color:{c["text_hint"]};font-size:13px;">No lessons this week.</span>'

    # Math weak concept rows
    math_weak_rows = ""
    for w in data["math"]["weak_areas"]:
        math_weak_rows += f"""
        <tr>
          <td style="font-size:13px;color:{c['text']};padding:4px 0;">{w['lesson']}</td>
          <td style="font-size:12px;color:{c['error']};font-weight:700;
              padding:4px 0 4px 12px;">{w['wrong']} wrong</td>
        </tr>"""
    if not math_weak_rows:
        math_weak_rows = f'<tr><td colspan="2" style="font-size:13px;color:{c["success_ink"]};padding:4px 0;">No weak areas this week!</td></tr>'

    # Math daily progress bar
    math_d_done  = data["math"]["daily_done"]
    math_d_total = max(data["math"]["daily_total"], 1)
    math_d_pct   = int(math_d_done / math_d_total * 100)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly Report — {child_name}</title>
</head>
<body style="margin:0;padding:0;background:{c['page']};
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0"
  style="background:{c['page']};padding:32px 16px;">
<tr><td>
<table width="600" cellpadding="0" cellspacing="0" align="center"
  style="background:{c['card']};border-radius:16px;overflow:hidden;
         border:1px solid {c['border']};
         box-shadow:0 2px 8px rgba(120,90,60,0.08);">

  <!-- ── Header ───────────────────────────────── -->
  <tr>
    <td style="background:{c['primary']};padding:28px 40px;text-align:center;">
      <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;
           color:rgba(255,255,255,0.8);text-transform:uppercase;margin-bottom:6px;">
        Weekly Learning Report
      </div>
      <div style="font-size:26px;font-weight:700;color:{c['text_on']};margin-bottom:4px;">
        {child_name}'s Progress
      </div>
      <div style="font-size:13px;color:rgba(255,255,255,0.75);">
        {data['week_label']}
      </div>
    </td>
  </tr>

  <!-- ── Summary cards ────────────────────────── -->
  <tr>
    <td style="padding:28px 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="text-align:center;padding:16px 6px;
              background:{c['eng_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['eng']};">{data['week_xp']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">XP This Week</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['success_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['success_ink']};">{data['words_correct']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Words Mastered</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['arcade_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['arcade_ink']};">{data['streak']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Day Streak</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['rewards_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['rewards']};">{data['total_minutes']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Min Studied</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── Body ─────────────────────────────────── -->
  <tr><td style="padding:0 40px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0">

      <!-- Daily activity chart -->
      {_section_header("Daily Activity", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr>
        <td>
          <table cellpadding="0" cellspacing="0" style="height:80px;">
            <tr style="vertical-align:bottom;">{day_bars}</tr>
          </table>
        </td>
      </tr>

      <!-- English section -->
      {_section_header("English — Stage Performance", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {stage_rows}
          </table>
        </td>
      </tr>

      <!-- Weak words -->
      {_section_header("Words Needing Practice", c['error'], c['error_light'], c['error_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {weak_rows}
          </table>
        </td>
      </tr>

      <!-- Lessons studied -->
      {_section_header("Lessons Studied", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr><td style="padding-bottom:8px;">{lesson_tags}</td></tr>

      <!-- Math section -->
      {_section_header("Math", c['math'], c['math_light'], c['math_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">Accuracy (7 days)</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">{data['math']['accuracy_pct']}%</td>
            </tr>
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">Daily Challenge</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">
                {math_d_done} / {data['math']['daily_total']} days
              </td>
            </tr>
            <tr>
              <td colspan="2" style="padding:6px 0 2px;">
                <div style="background:{c['border_sub']};border-radius:4px;height:6px;">
                  <div style="background:{c['math']};width:{math_d_pct}%;
                       height:6px;border-radius:4px;"></div>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0 4px;font-size:13px;color:{c['text_sub']};">
                Wrong Review pending</td>
              <td style="padding:8px 0 4px;font-size:13px;font-weight:700;
                  color:{c['error']};text-align:right;">
                {data['math']['wrong_pending']} items
              </td>
            </tr>
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">
                Fact Fluency best</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">
                {data['math']['best_fluency']} pts
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Math weak areas -->
      {_section_header("Math — Weak Areas", c['math'], c['math_light'], c['math_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {math_weak_rows}
          </table>
        </td>
      </tr>

      <!-- CKLA section -->
      {_ckla_section(data.get('ckla', {}), c)}

      <!-- Overall stats -->
      {_section_header("Overall Progress", c['primary'], c['rewards_light'], c['text'])}
      <tr>
        <td style="background:{c['surface']};border-radius:12px;padding:16px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">Total XP</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['total_xp']:,} XP</td>
            </tr>
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">
                Avg Accuracy</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['avg_accuracy']}%</td>
            </tr>
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">Sessions</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['total_sessions']}</td>
            </tr>
          </table>
        </td>
      </tr>

    </table>
  </td></tr>

  <!-- ── Footer ───────────────────────────────── -->
  <tr>
    <td style="background:{c['surface']};padding:16px 40px;text-align:center;
        border-top:1px solid {c['border_sub']};">
      <div style="font-size:11px;color:{c['text_hint']};">
        NSS Word Master · Weekly Report · Auto-generated
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html
