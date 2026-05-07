#!/usr/bin/env python3
"""
verify_g3_new_units.py — Re-compute answers for U11/U12/U13 problems and
flag mismatches with the stored correct_answer field.

Usage:  python3 scripts/verify_g3_new_units.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend" / "data" / "math" / "G3"
UNITS = ["U11_time_mass_volume", "U12_area", "U13_shapes"]

# ---------- helpers ----------------------------------------------------------

POLYGON_SIDES = {
    "triangle": 3, "quadrilateral": 4, "pentagon": 5,
    "hexagon": 6, "heptagon": 7, "octagon": 8,
}


def norm(v):
    """Normalize an answer for comparison: strip MC prefix and common unit suffixes."""
    if v is None:
        return ""
    s = str(v).strip()
    # Strip MC choice prefix
    m = re.match(r"^[A-D]\)\s*(.+)$", s)
    if m:
        s = m.group(1).strip()
    s = s.lower()
    # Strip common unit suffixes for numerical comparison
    units_re = r"\s+(?:square units?|sq units?|square (?:cm|centimeters?|m|meters?|inches?)|sq (?:cm|m)|grams?|g|kilograms?|kg|milliliters?|ml|liters?|l|minutes?|min|hours?|hr|sides?|cm|meters?|m)\b\.?"
    s = re.sub(units_re, "", s).strip()
    return s


def parse_time(t):
    """'3:45' -> minutes since midnight."""
    m = re.match(r"^(\d{1,2}):(\d{2})$", t)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def fmt_time(mins):
    """Minutes -> 'H:MM'."""
    h = (mins // 60) % 24
    mm = mins % 60
    return f"{h}:{mm:02d}"


# ---------- solvers (return None if can't handle) ---------------------------

def solve_pure_arithmetic(q):
    """'324 + 276 = ?' / '7 × 8 = ?' / '54 ÷ 9 = ?'"""
    s = q.replace("−", "-").replace("×", "*").replace("÷", "/").replace(",", "")
    m = re.match(r"^\s*(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*\??\s*$", s)
    if not m:
        return None
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    if op == "+": return str(a + b)
    if op == "-": return str(a - b)
    if op == "*": return str(a * b)
    if op == "/": return str(a // b) if b and a % b == 0 else None
    return None


def solve_unit_conversion(q):
    """'1 kg = ___ g', '5000 g = ___ kg', '1 L = ___ mL', '2000 mL = ___ L'"""
    s = q.strip().replace(",", "")
    m = re.match(r"^\s*(\d+)\s*(kg|g|L|mL)\s*=\s*_+\s*(kg|g|L|mL)", s)
    if not m:
        return None
    n, src, dst = int(m.group(1)), m.group(2), m.group(3)
    pairs = {("kg", "g"): 1000, ("g", "kg"): 1/1000,
             ("L", "mL"): 1000, ("mL", "L"): 1/1000}
    factor = pairs.get((src, dst))
    if factor is None:
        return None
    val = n * factor
    if val == int(val):
        return str(int(val))
    return None


def solve_polygon_sides(q):
    """'How many sides does a hexagon have?' / 'A pentagon has how many sides?'"""
    s = q.lower()
    if "how many sides" not in s and "how many vertices" not in s and "how many angles" not in s:
        return None
    for name, n in POLYGON_SIDES.items():
        if name in s:
            return str(n)
    return None


def solve_polygon_name_from_count(q):
    """'A polygon with 6 sides is called?'  (helps MC where answer is a name)"""
    m = re.search(r"(\d+)\s+sides", q.lower())
    if not m:
        return None
    n = int(m.group(1))
    inv = {v: k for k, v in POLYGON_SIDES.items()}
    return inv.get(n)


def solve_round(q):
    """'Round 347 to the nearest hundred' / 'Round 66 to nearest ten'"""
    m = re.match(r"^Round\s+(\d+)\s+to\s+the\s+nearest\s+(ten|hundred)\.?\s*$", q.strip())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    base = 10 if unit == "ten" else 100
    # round half up
    r = ((n + base // 2) // base) * base
    return str(r)


def solve_elapsed_same_hour(q):
    """'From 5:10 to 5:45. Minutes?' / 'From 2:00 to 5:00, how many hours?'"""
    m = re.search(r"From\s+(\d{1,2}:\d{2})\s+to\s+(\d{1,2}:\d{2})", q)
    if not m:
        return None
    t1 = parse_time(m.group(1))
    t2 = parse_time(m.group(2))
    if t1 is None or t2 is None:
        return None
    diff = t2 - t1
    if diff < 0:
        diff += 12 * 60  # handle 12-hour wrap (e.g. 9:00 -> 1:00)
    # Detect if question asks for hours vs minutes
    ql = q.lower()
    asks_hours = "hour" in ql and "minute" not in ql
    if asks_hours:
        if diff % 60 == 0:
            return str(diff // 60)
        return None  # mixed unit, skip
    return str(diff)


def solve_square_metric(q):
    """Square with side N. Disambiguate area vs perimeter from question text."""
    m = re.search(r"square\s+(?:has\s+)?sides?\s+(\d+)\s*cm", q, re.I)
    if not m:
        return None
    s = int(m.group(1))
    ql = q.lower()
    if "area" in ql:
        return str(s * s)
    if "perimeter" in ql:
        return str(4 * s)
    return None


def solve_area_grid(q):
    """'rectangle has 4 rows and 7 columns' / '3 rows × 5 columns' / '4 rows of 5 unit squares'."""
    ql = q.lower()
    if not re.search(r"area|how many\s+(?:unit )?squares?", ql):
        return None
    if _is_multi_step(q):
        return None
    # Frame/border problems — multi-step
    if re.search(r"\b(?:frame|border|all around|extra)\b", ql):
        return None
    pats = [
        r"(\d+)\s+rows?\s+(?:and|×|x|by)\s+(\d+)\s+columns?",
        r"(\d+)\s+columns?\s+(?:and|×|x|by)\s+(\d+)\s+rows?",
        r"(\d+)\s+rows?\s+of\s+(\d+)",
        r"(\d+)\s+rows?\s*[×x]\s*(\d+)\s+columns?",
        r"(\d+)\s+rows?\s*×\s*(\d+)",
        r"(\d+)\s*rows?\s+with\s+(\d+)",
        r"each row has\s+(\d+).*?(\d+)\s+rows",
    ]
    for p in pats:
        m = re.search(p, ql)
        if m:
            return str(int(m.group(1)) * int(m.group(2)))
    # "X rows. Each row has Y" — different order
    m = re.search(r"(\d+)\s+rows?.*?each row has\s+(\d+)", ql, re.S)
    if m:
        return str(int(m.group(1)) * int(m.group(2)))
    # "Y wide and X tall in unit squares"
    m = re.search(r"(\d+)\s+unit squares?\s+wide\s+and\s+(\d+)\s+unit squares?\s+tall", ql)
    if m:
        return str(int(m.group(1)) * int(m.group(2)))
    return None


def solve_area_unit_squares(q):
    """'A figure is covered by 12 unit squares. Area?' → 12. Skip conceptual MC."""
    ql = q.lower()
    if not re.search(r"area", ql):
        return None
    if _is_multi_step(q):
        return None
    # Conceptual / MC indicator phrases — skip
    if re.search(r"\b(?:best way|which method|which way|how (?:do|can) you|why)\b", ql):
        return None
    m = re.search(r"covered by\s+(\d+)\s+unit squares?", ql)
    if m:
        return str(int(m.group(1)))
    m = re.search(r"made of\s+(\d+)\s+unit squares?", ql)
    if m:
        return str(int(m.group(1)))
    return None


def solve_area_combined(q):
    """'split into A×B AND C×D. Total area?' — sum the splits.
    'A 4×9 rectangle splits into 4×5 and 4×4' → ignore the leading 4×9."""
    ql = q.lower()
    if not re.search(r"total area|combined area", ql):
        return None
    # Find all NxM patterns and their positions
    matches = list(re.finditer(r"(\d+)\s*[×x]\s*(\d+)", ql))
    if len(matches) < 2:
        return None
    # If "splits into" / "split into" appears, use only patterns AFTER that phrase
    split_marker = re.search(r"splits?\s+into|made of|consists of", ql)
    if split_marker:
        cutoff = split_marker.end()
        matches = [m for m in matches if m.start() >= cutoff]
        if len(matches) < 2:
            return None
    total = sum(int(m.group(1)) * int(m.group(2)) for m in matches)
    return str(total)


def solve_area_rect(q):
    """'A rectangle is 6 cm long and 4 cm wide. What is its area?'
       'A rectangle is 6 cm by 4 cm.'"""
    ql = q.lower()
    if "area" not in ql:
        return None
    m = re.search(r"rectangle.*?(\d+)\s*cm\s+(?:long|wide|tall)\s+and\s+(\d+)\s*cm\s+(?:long|wide|tall)", q, re.I | re.S)
    if not m:
        m = re.search(r"rectangle.*?(\d+)\s*cm\s*(?:by|x|×)\s*(\d+)\s*cm", q, re.I | re.S)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return str(a * b)


def solve_polygon_combined(q):
    """'X and Y together' / 'X and Y all together' — sum of polygon side counts."""
    ql = q.lower()
    if not re.search(r"how many\s+sides", ql):
        return None
    if not re.search(r"\b(together|all together|altogether|combined|both)\b", ql):
        return None
    found = []
    for name, n in POLYGON_SIDES.items():
        # Count occurrences in question
        for _ in re.finditer(rf"\b{name}\b", ql):
            found.append(n)
    if len(found) >= 2:
        return str(sum(found))
    return None


def solve_polygon_difference(q):
    """'Two polygons together have N sides. One is X. How many sides does the OTHER?'"""
    ql = q.lower()
    if "other polygon" not in ql and "other shape" not in ql:
        return None
    m = re.search(r"have\s+(\d+)\s+sides", ql)
    if not m:
        return None
    total = int(m.group(1))
    for name, n in POLYGON_SIDES.items():
        if name in ql:
            return str(total - n)
    return None


def solve_polygon_sum_named(q):
    """'has the same number of sides as a HEXAGON plus a TRIANGLE'"""
    ql = q.lower()
    if "plus a" not in ql and "plus an" not in ql:
        return None
    found = [n for name, n in POLYGON_SIDES.items() if name in ql]
    if len(found) >= 2:
        return str(sum(found))
    return None


def solve_kg_to_g(q):
    """'A watermelon weighs 3 kg. How many grams is that?'"""
    m = re.search(r"(\d+)\s*kg.*how many gram", q, re.I | re.S)
    if not m:
        return None
    return str(int(m.group(1)) * 1000)


def solve_l_to_ml(q):
    """'2 L = ___ mL'-style or 'X liters... how many milliliters'"""
    m = re.search(r"(\d+)\s*(?:L|liters?).*how many\s*(?:mL|milliliters?)", q, re.I | re.S)
    if not m:
        return None
    return str(int(m.group(1)) * 1000)


def solve_multiplication_unknown(q):
    """'If 4 × n = 28, then n = ?' / '4 × n = 28'"""
    s = q.replace("×", "*")
    m = re.search(r"(\d+)\s*\*\s*n\s*=\s*(\d+)", s)
    if not m:
        return None
    a, p = int(m.group(1)), int(m.group(2))
    if a and p % a == 0:
        return str(p // a)
    return None


def solve_division_unknown(q):
    """'? ÷ 8 = 6' / '? / 8 = 6' / 'X ÷ 8 = 6 missing number'"""
    s = q.replace("÷", "/")
    m = re.search(r"\?\s*/\s*(\d+)\s*=\s*(\d+)", s)
    if not m:
        return None
    return str(int(m.group(1)) * int(m.group(2)))


def solve_minute_hand_on(q):
    """'Minute hand on 6 = how many minutes?' / 'If minute hand is on the 4...'"""
    ql = q.lower()
    if "minute hand" not in ql or "tick" in ql:
        return None
    m = re.search(r"minute hand (?:is )?on (?:the )?(\d{1,2})", ql)
    if not m:
        return None
    n = int(m.group(1))
    if n == 12:
        return "0"
    if 1 <= n <= 11:
        return str(n * 5)
    return None


def solve_minute_hand_ticks(q):
    """'Minute hand 2 ticks past 7. How many minutes?'  → 35 + 2 = 37"""
    ql = q.lower()
    m = re.search(r"minute hand (\d+)\s+ticks?\s+past (?:the )?(\d{1,2})", ql)
    if not m:
        return None
    ticks, num = int(m.group(1)), int(m.group(2))
    if num == 12:
        base = 0
    elif 1 <= num <= 11:
        base = num * 5
    else:
        return None
    return str(base + ticks)


def solve_hour_min_to_minutes(q):
    """'How many minutes in 2 hours?' / 'in 1 hour 20 minutes?'"""
    ql = q.lower()
    if not re.search(r"how many minutes? (?:are )?in", ql) and "minutes in" not in ql:
        return None
    m = re.search(r"(\d+)\s+hours?\s+(\d+)\s+min", ql)
    if m:
        return str(int(m.group(1)) * 60 + int(m.group(2)))
    m = re.search(r"(\d+)\s+hours?", ql)
    if m and "minute" not in ql.replace("minutes in", "").replace("minutes are", ""):
        # plain "N hours"
        return str(int(m.group(1)) * 60)
    if m:
        return str(int(m.group(1)) * 60)
    return None


def solve_hour_hand_time(q):
    """'Hour hand between 3 and 4. Minute hand on 6.' → 3:30
       'Hour hand just before 5. Minute hand 2 ticks past 11.' → 4:57"""
    ql = q.lower()
    h = re.search(r"hour hand (?:is )?between (\d{1,2}) and (\d{1,2})", ql)
    if h:
        h1 = int(h.group(1))
    else:
        h2 = re.search(r"hour hand (?:is )?just before (\d{1,2})", ql)
        if h2:
            n = int(h2.group(1))
            h1 = 12 if n == 1 else n - 1
        else:
            h3 = re.search(r"hour hand (?:is )?just (?:after|past) (?:the )?(\d{1,2})", ql)
            if h3:
                h1 = int(h3.group(1))
            else:
                return None
    # Need minute info
    m_on = re.search(r"minute hand (?:is )?on (?:the )?(\d{1,2})", ql)
    m_tick = re.search(r"minute hand (\d+)\s+ticks?\s+past (?:the )?(\d{1,2})", ql)
    if m_tick:
        ticks, num = int(m_tick.group(1)), int(m_tick.group(2))
        mins = (0 if num == 12 else num * 5) + ticks
    elif m_on:
        n = int(m_on.group(1))
        mins = 0 if n == 12 else n * 5
    else:
        return None
    return f"{h1}:{mins:02d}"


def solve_start_plus_duration(q):
    """'starts at H:MM and works for N minutes. End time?'
       'School starts 8:00 and lasts 90 min. End time?'"""
    ql = q.lower()
    if "end time" not in ql and "end?" not in ql:
        return None
    m = re.search(r"(?:starts?|begin[s]?|opens?)\s+(?:at\s+)?(\d{1,2}:\d{2})", ql)
    if not m:
        return None
    start = parse_time(m.group(1))
    if start is None:
        return None
    # Duration: "for N minutes" / "lasts N minutes" / "lasts? N min" / "N minutes long"
    d = re.search(r"(?:for|lasts?|long)\s+(\d+)\s*hour[s]?\s*(\d+)?\s*min", ql)
    if d:
        dur = int(d.group(1)) * 60 + (int(d.group(2)) if d.group(2) else 0)
    else:
        d = re.search(r"(?:for|lasts?)\s+(\d+)\s*min", ql)
        if d:
            dur = int(d.group(1))
        else:
            d = re.search(r"(\d+)\s*minutes? long", ql)
            if d:
                dur = int(d.group(1))
            else:
                d = re.search(r"(?:for|lasts?)\s+(\d+)\s*hour", ql)
                if d:
                    dur = int(d.group(1)) * 60
                else:
                    return None
    end = start + dur
    return fmt_time(end)


def solve_end_minus_duration(q):
    """'ends at H:MM. It was N minutes long. Start time?' / 'finished at H:MM. He worked for N min.'"""
    ql = q.lower()
    if "start time" not in ql and "start?" not in ql:
        return None
    m = re.search(r"(?:ends?|ended|finish(?:ed|es)?)\s+(?:at\s+)?(\d{1,2}:\d{2})", ql)
    if not m:
        return None
    end = parse_time(m.group(1))
    if end is None:
        return None
    d = re.search(r"(\d+)\s*hour[s]?\s*(\d+)?\s*min", ql)
    if d:
        dur = int(d.group(1)) * 60 + (int(d.group(2)) if d.group(2) else 0)
    else:
        d = re.search(r"(?:was|for|lasted|long)\s+(\d+)\s*min", ql)
        if d:
            dur = int(d.group(1))
        else:
            d = re.search(r"(\d+)\s*minutes? long", ql)
            if d:
                dur = int(d.group(1))
            else:
                d = re.search(r"(\d+)\s*hour[s]?\s*long", ql)
                if d:
                    dur = int(d.group(1)) * 60
                else:
                    return None
    start = end - dur
    return fmt_time(start)


def solve_elapsed_anywhere(q):
    """'starts at X and ends at Y' / 'from X to Y' / 'X to Y P.M.' — total minutes.
    If 4 timestamps and question asks 'total active time' → sum both intervals."""
    ql = q.lower()
    if not re.search(r"(?:total minutes?|how many minutes)", ql):
        # "how long?" alone is ambiguous (could be hours/minutes/mixed) → skip
        return None
    if "hour" in ql and "minute" not in ql:
        return None
    times = re.findall(r"(\d{1,2}:\d{2})", q)
    if len(times) < 2:
        return None
    # 4 timestamps + "total" / "active" → sum two intervals
    if len(times) >= 4 and re.search(r"(?:total|active)", ql):
        t = [parse_time(x) for x in times[:4]]
        if any(x is None for x in t):
            return None
        d1 = t[1] - t[0]
        if d1 < 0: d1 += 12 * 60
        d2 = t[3] - t[2]
        if d2 < 0: d2 += 12 * 60
        return str(d1 + d2)
    if len(times) >= 3:
        return None  # ambiguous
    t1 = parse_time(times[0])
    t2 = parse_time(times[1])
    if t1 is None or t2 is None:
        return None
    diff = t2 - t1
    if diff < 0:
        diff += 12 * 60
    return str(diff)


def solve_groups_of(q):
    """'X bags of Y items each' / 'X groups with Y' / 'X rows of Y' — multiplication"""
    ql = q.lower()
    # Pattern: "N (bags|groups|boxes|rows|...) (of|with) M (items|each)"
    m = re.search(r"(\d+)\s+(?:bags?|groups?|boxes?|rows?|piles?|trays?|packs?|sets?|cups?|sacks?|baskets?)\s+(?:of|with)\s+(\d+)", ql)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    # Look for "total" / "how many" / "altogether" / "in all"
    if not re.search(r"(?:total|how many|altogether|in all)", ql):
        return None
    return str(a * b)


def _is_multi_step(q):
    """True if the question has multi-step structure that simple solvers can't handle."""
    ql = q.lower()
    # Multiple "then" indicates sequential steps
    if ql.count("then") >= 1 and re.search(r"\d", ql):
        return True
    # "each" alongside two distinct numeric quantities suggests N × M before subtract
    if "each" in ql:
        nums = re.findall(r"\d+", ql)
        if len(nums) >= 3:
            return True
    # Decimal numbers — current solvers handle integer only
    if re.search(r"\d+\.\d+", q):
        return True
    return False


def solve_how_many_unit_in(q):
    """'How many g in 5 kg?' / 'How many mL in 4 L?' / 'How many kg in 2000 g?'
       'How many g in 4 kg 500 g?' / '1 kilogram = ___ grams.'"""
    if re.search(r"\d+\.\d+", q):
        return None  # decimals not handled
    ql = q.lower().replace(",", "")
    # Patterns: kg→g, g→kg, L→mL, mL→L
    pairs = [
        (r"how many\s+(?:g|grams?)\s+in\s+(\d+)\s*(?:kg|kilograms?)\s+(\d+)\s*(?:g|grams?)", lambda m: int(m.group(1)) * 1000 + int(m.group(2))),
        (r"how many\s+(?:mL|milliliters?)\s+in\s+(\d+)\s*(?:L|liters?)\s+(\d+)\s*(?:mL|milliliters?)", lambda m: int(m.group(1)) * 1000 + int(m.group(2))),
        (r"how many\s+(?:g|grams?)\s+in\s+(\d+)\s*(?:kg|kilograms?)", lambda m: int(m.group(1)) * 1000),
        (r"how many\s+(?:mL|milliliters?)\s+in\s+(\d+)\s*(?:L|liters?)", lambda m: int(m.group(1)) * 1000),
        (r"how many\s+(?:kg|kilograms?)\s+in\s+(\d+)\s*(?:g|grams?)", lambda m: int(m.group(1)) // 1000 if int(m.group(1)) % 1000 == 0 else None),
        (r"how many\s+(?:L|liters?)\s+in\s+(\d+)\s*(?:mL|milliliters?)", lambda m: int(m.group(1)) // 1000 if int(m.group(1)) % 1000 == 0 else None),
        (r"(\d+)\s*(?:kg|kilograms?)\s*=\s*_+\s*(?:g|grams?)", lambda m: int(m.group(1)) * 1000),
        (r"(\d+)\s*(?:L|liters?)\s*=\s*_+\s*(?:mL|milliliters?)", lambda m: int(m.group(1)) * 1000),
        (r"(\d+)\s*(?:kilogram|kilometre)s?\s*=\s*_+\s*(?:gram|metre)s?", lambda m: int(m.group(1)) * 1000),
        (r"(\d+)\s*(?:liter)s?\s*=\s*_+\s*(?:milliliter)s?", lambda m: int(m.group(1)) * 1000),
    ]
    for pat, fn in pairs:
        m = re.search(pat, ql)
        if m:
            v = fn(m)
            if v is None:
                return None
            return str(v)
    return None


def solve_mass_or_volume_arith(q):
    """'200 g + 350 g' / 'X kg + Y kg' / 'X mL - Y mL' / etc."""
    s = q.replace("−", "-")
    ql = s.lower().replace(",", "")
    # Same-unit add/subtract: "200 g + 350 g" / "1000 mL - 350 mL" / "5 kg + 6 kg"
    for unit in ["mL", "milliliters?", "L", "liters?", "g", "grams?", "kg", "kilograms?"]:
        pat = rf"(\d+)\s*{unit}\s*([+\-])\s*(\d+)\s*{unit}"
        m = re.search(pat, ql)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            return str(a + b if op == "+" else a - b)
    return None


def solve_each_total(q):
    """'5 cups, each 200 mL. Total?' / 'N items, each X. Total?'"""
    ql = q.lower()
    if not re.search(r"(?:total|in all|altogether)", ql):
        return None
    if _is_multi_step(q):
        return None
    # "5 cups, each 200 mL"
    m = re.search(r"(\d+)\s+\w+,?\s+each\s+(\d+)\s*(?:g|kg|mL|L|grams?|kilograms?|milliliters?|liters?|apples?|cookies?|items?|books?|boxes?)", ql)
    if not m:
        return None
    return str(int(m.group(1)) * int(m.group(2)))


def solve_n_groups_of(q):
    """'5 boxes, each 6 kg. Total?' — strict total-only with two numbers."""
    ql = q.lower()
    if not re.search(r"(?:total|in all|altogether)", ql):
        return None
    if _is_multi_step(q):
        return None
    m = re.search(r"(\d+)\s+(?:bags?|groups?|boxes?|rows?|jugs?|cups?|cookies?|books?|piles?|trays?|packs?|sets?)\s*(?:,\s*each|of)\s+(\d+)\s*(?:kg|g|mL|L|grams?|kilograms?|milliliters?|liters?)", ql)
    if not m:
        return None
    return str(int(m.group(1)) * int(m.group(2)))


def solve_left_after(q):
    """'Bottle has 1000 mL. Pour out 250 mL. Left?' — strict 2-number version only."""
    ql = q.lower()
    if "left" not in ql and "remain" not in ql:
        return None
    if _is_multi_step(q):
        return None
    nums = re.findall(r"(\d+)\s*(g|kg|mL|L|grams?|kilograms?|milliliters?|liters?)", q.replace(",", ""))
    if len(nums) != 2:
        return None  # exactly two numbers
    n1, u1 = int(nums[0][0]), nums[0][1].lower()
    n2, u2 = int(nums[1][0]), nums[1][1].lower()
    def nrm(u):
        return {"g": "g", "grams": "g", "gram": "g",
                "kg": "kg", "kilogram": "kg", "kilograms": "kg",
                "ml": "mL", "milliliter": "mL", "milliliters": "mL",
                "l": "L", "liter": "L", "liters": "L"}.get(u, u)
    u1n, u2n = nrm(u1), nrm(u2)
    if u1n != u2n:
        return None  # cross-unit too ambiguous
    # Determine larger - smaller (assumes "left" means start - taken away)
    larger, smaller = max(n1, n2), min(n1, n2)
    return str(larger - smaller)


def solve_total_two_items(q):
    """'Tom 200 g, Sara 250 g. Total?' — strict same-unit 2-number sum."""
    ql = q.lower()
    if not re.search(r"(?:total|in all|combined|altogether)", ql):
        return None
    if _is_multi_step(q):
        return None
    if "each" in ql:
        return None  # multiplication scenarios are handled by other solvers
    # Find all "N <unit>" pairs with same unit
    pairs = re.findall(r"(\d+)\s*(g|kg|mL|L|grams?|kilograms?|milliliters?|liters?)\b", q.replace(",", ""))
    if len(pairs) < 2:
        return None
    def nrm(u):
        u = u.lower()
        return {"grams": "g", "gram": "g", "kilograms": "kg", "kilogram": "kg",
                "milliliters": "mL", "milliliter": "mL", "liters": "L", "liter": "L"}.get(u, u)
    units = [nrm(u) for _, u in pairs]
    if all(x == units[0] for x in units) and len(pairs) == 2:
        return str(int(pairs[0][0]) + int(pairs[1][0]))
    return None


def solve_how_much_more(q):
    """'Lily pours 800 mL. Mia pours 500 mL. Lily pours how much MORE?' — same-unit 2-num only."""
    ql = q.lower()
    if not re.search(r"how much (?:more|heavier|less|lighter|extra)", ql):
        return None
    if _is_multi_step(q):
        return None
    nums = re.findall(r"(\d+)\s*(g|kg|mL|L|grams?|kilograms?|milliliters?|liters?)\b", q.replace(",", ""))
    if len(nums) != 2:
        return None
    def nrm(u):
        u = u.lower()
        return {"grams": "g", "gram": "g", "kilograms": "kg", "kilogram": "kg",
                "milliliters": "mL", "milliliter": "mL", "liters": "L", "liter": "L"}.get(u, u)
    if nrm(nums[0][1]) != nrm(nums[1][1]):
        return None
    a, b = int(nums[0][0]), int(nums[1][0])
    return str(abs(a - b))


def solve_share_into(q):
    """'X items shared (equally )?into N groups/bags/cups' — division"""
    ql = q.lower()
    m = re.search(r"(\d+)\s+(?:cookies|apples|oranges|items|kg|g|mL|liters?|kilograms?|grams?)\s+(?:shared|split|divided|put)\s+(?:equally\s+)?(?:into|among)\s+(\d+)", ql)
    if not m:
        return None
    total, n = int(m.group(1)), int(m.group(2))
    if n and total % n == 0:
        return str(total // n)
    return None


SOLVERS = [
    # Order matters: more specific solvers should run before generic ones
    ("polygon_combined", solve_polygon_combined),
    ("polygon_difference", solve_polygon_difference),
    ("polygon_sum_named", solve_polygon_sum_named),
    ("hour_hand_time", solve_hour_hand_time),
    ("minute_hand_ticks", solve_minute_hand_ticks),
    ("minute_hand_on", solve_minute_hand_on),
    ("hour_min_to_minutes", solve_hour_min_to_minutes),
    ("start_plus_duration", solve_start_plus_duration),
    ("end_minus_duration", solve_end_minus_duration),
    ("how_much_more", solve_how_much_more),
    ("left_after", solve_left_after),
    ("total_two_items", solve_total_two_items),
    ("each_total", solve_each_total),
    ("n_groups_of", solve_n_groups_of),
    ("how_many_unit_in", solve_how_many_unit_in),
    ("mass_vol_arith", solve_mass_or_volume_arith),
    ("share_into", solve_share_into),
    ("groups_of", solve_groups_of),
    ("arithmetic", solve_pure_arithmetic),
    ("conversion", solve_unit_conversion),
    ("polygon_sides", solve_polygon_sides),
    ("round", solve_round),
    ("elapsed_same", solve_elapsed_same_hour),
    ("elapsed_anywhere", solve_elapsed_anywhere),
    ("area_combined", solve_area_combined),
    ("area_grid", solve_area_grid),
    ("area_unit_squares", solve_area_unit_squares),
    ("square_metric", solve_square_metric),
    ("area_rect", solve_area_rect),
    ("kg_to_g", solve_kg_to_g),
    ("l_to_ml", solve_l_to_ml),
    ("mul_unknown", solve_multiplication_unknown),
    ("div_unknown", solve_division_unknown),
]


def try_solve(q):
    """Try each solver. Return (solver_name, computed) or (None, None)."""
    for name, fn in SOLVERS:
        try:
            r = fn(q)
        except Exception:
            r = None
        if r is not None:
            return name, r
    return None, None


# ---------- mc helper --------------------------------------------------------

def resolve_mc_answer(item):
    """For MC items, correct_answer is 'B'. Return the actual text after 'B) '."""
    ans = item.get("correct_answer", "")
    choices = item.get("choices") or []
    if item.get("type") == "mc" and ans in ("A", "B", "C", "D"):
        idx = ord(ans) - ord("A")
        if idx < len(choices):
            return choices[idx]
    return ans


# ---------- main -------------------------------------------------------------

def iter_problems(data, file_name):
    """Yield (stage, item) for every gradable item in a lesson or unit_test."""
    if "problems" in data:  # unit_test
        for p in data["problems"]:
            yield "problems", p
        return
    for stage in ["pretest", "try", "practice_r1", "practice_r2", "practice_r3"]:
        for p in data.get(stage, []):
            yield stage, p


def main():
    files = []
    for u in UNITS:
        for f in sorted((ROOT / u).glob("*.json")):
            files.append(f)

    total = 0
    verified = 0
    mismatches = []
    skipped_types = {}

    for f in files:
        data = json.loads(f.read_text())
        rel = f.relative_to(ROOT.parent)
        for stage, item in iter_problems(data, f.name):
            total += 1
            qtype = item.get("type", "?")
            q = item.get("question", "")
            # For MC, resolve the actual text answer; for others, use correct_answer raw
            stored = resolve_mc_answer(item)
            # Skip true/false (numeric solvers will misfire on them)
            if qtype == "tf":
                skipped_types[qtype] = skipped_types.get(qtype, 0) + 1
                continue
            solver, computed = try_solve(q)
            if computed is None:
                skipped_types[qtype] = skipped_types.get(qtype, 0) + 1
                continue
            verified += 1
            if norm(stored) != norm(computed):
                mismatches.append({
                    "file": str(rel),
                    "stage": stage,
                    "id": item.get("id"),
                    "question": q,
                    "stored_answer": stored,
                    "computed_answer": computed,
                    "solver": solver,
                })

    print(f"\n{'=' * 70}")
    print(f"  Verification report — G3 U11/U12/U13")
    print(f"{'=' * 70}")
    print(f"  Files scanned:          {len(files)}")
    print(f"  Total problems:         {total}")
    print(f"  Auto-verified:          {verified}  ({verified / total * 100:.1f}%)")
    print(f"  Skipped (no solver):    {total - verified}")
    print(f"  Mismatches found:       {len(mismatches)}")
    print(f"{'=' * 70}\n")

    if mismatches:
        print("MISMATCHES:")
        for i, m in enumerate(mismatches, 1):
            print(f"\n[{i}] {m['file']} -> {m['stage']} {m['id']}  ({m['solver']})")
            print(f"    Q: {m['question'][:120]}")
            print(f"    Stored:   {m['stored_answer']!r}")
            print(f"    Computed: {m['computed_answer']!r}")
    else:
        print("No mismatches in auto-verifiable problems.")

    if "--dump-skipped" in sys.argv:
        out = []
        for f in files:
            data = json.loads(f.read_text())
            for stage, item in iter_problems(data, f.name):
                if item.get("type") == "tf":
                    pass  # include T/F too
                solver, computed = try_solve(item.get("question", ""))
                if computed is None:
                    out.append({
                        "file": str(f.relative_to(ROOT.parent)),
                        "stage": stage,
                        "id": item.get("id"),
                        "type": item.get("type"),
                        "question": item.get("question", ""),
                        "choices": item.get("choices"),
                        "correct_answer": item.get("correct_answer"),
                        "stored_resolved": resolve_mc_answer(item),
                    })
        Path("scripts/skipped_problems.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False)
        )
        print(f"\nDumped {len(out)} skipped problems to scripts/skipped_problems.json")

    if "--show-skipped" in sys.argv:
        print(f"\nSkipped by type: {skipped_types}")
        print("\nSample of unverified questions (50):")
        n = 0
        for f in files:
            data = json.loads(f.read_text())
            for stage, item in iter_problems(data, f.name):
                if item.get("type") == "tf":
                    continue
                solver, computed = try_solve(item.get("question", ""))
                if computed is None and item.get("type") in ("input", "mc"):
                    n += 1
                    if n <= 50:
                        print(f"  [{n:3d}] {f.name} {stage} {item.get('id')}: {item.get('question','')[:90]}")
                    if n >= 50:
                        break
            if n >= 50:
                break

    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
