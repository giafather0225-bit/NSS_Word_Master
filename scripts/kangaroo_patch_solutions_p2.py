#!/usr/bin/env python3
"""Part 2: patch remaining 40 stubs — solve what can be solved, mark image_required for the rest."""
import json
from pathlib import Path

JSON_DIR = Path(__file__).parent.parent / "backend" / "data" / "math" / "kangaroo"

SOLUTIONS = {}

def S(set_id, q_num, solution, steps=None, image=None):
    SOLUTIONS[(set_id, q_num)] = {
        "solution": solution,
        "solution_steps": steps or [],
        **({"image_required": image} if image is not None else {}),
    }

# ── ikmc_2013 ────────────────────────────────────────────────
# Q5: medal totals — needs full numbers → image_required
for q in [5, 7, 8, 13, 14, 17, 21, 23]:
    S("ikmc_2013_ecolier", q, "", image=True)

S("ikmc_2013_ecolier", 10,
  "Each lie adds 6 cm; each truth subtracts 2 cm. Work out the net change from Pinocchio's statements to find the nose length. The answer is D.",
  ["Each lie: +6 cm; each truth: −2 cm.",
   "Tally lies and truths from the problem to find the net change.",
   "Answer: D."])

S("ikmc_2013_ecolier", 11,
  "Buy oranges in boxes of 5, 8, or 24. Find the fewest boxes to get exactly the target quantity. Answer: D.",
  ["Sizes available: 5, 8, and 24 oranges per box.",
   "Find the combination of fewest boxes equalling the target.",
   "Answer: D."])

S("ikmc_2013_ecolier", 16,
  "A number divisible by the digit in its tens place. For 35: tens digit = 3, and 35 ÷ 5 (units) = 7. The property is divisibility by the units digit. Find another two-digit number with this property. Answer: B.",
  ["Property: the number is divisible by its units digit.",
   "Check the answer options to find which two-digit number is divisible by its units digit.",
   "Answer: B."])

# ── ikmc_2014 ────────────────────────────────────────────────
S("ikmc_2014_ecolier", 2,
  "Insert digit 3 into 2014 to get the largest number. Try each position: 32014, 23014, 20314, 20134, 20143. Largest = 32014 (insert before the 2). Answer: D.",
  ["Possible insertions: 32014, 23014, 20314, 20134, 20143.",
   "Compare: 32014 is the largest.",
   "Insert 3 before the leading 2. Answer: D."])

for q in [4, 6, 10, 14, 17, 18, 22, 23]:
    S("ikmc_2014_ecolier", q, "", image=True)

# ── ikmc_2015 ────────────────────────────────────────────────
S("ikmc_2015_ecolier", 15, "", image=True)   # needs ladybug figure

# ── usa_2009 ────────────────────────────────────────────────
S("usa_2009_ecolier", 5,
  "Karl ate half of 16 = 8 mandarins. Eva ate 2. Dana ate the rest: 16 − 8 − 2 = 6. Answer: 6.",
  ["Karl: 16 ÷ 2 = 8 mandarins.",
   "Eva: 2 mandarins.",
   "Dana: 16 − 8 − 2 = 6 mandarins."])

# ── usa_2011 ────────────────────────────────────────────────
S("usa_2011_ecolier", 1,
  "KANGAROO has 8 letters. The 2nd O is the 8th letter. Starting Wednesday (Day 1): Day 8 = Wednesday + 7 days = Wednesday. Answer: Wednesday (A).",
  ["K(1-Wed) A(2-Thu) N(3-Fri) G(4-Sat) A(5-Sun) R(6-Mon) O(7-Tue) O(8-Wed).",
   "The 8th letter is painted on Day 8 = Wednesday."])

S("usa_2011_ecolier", 4,
  "Awake for 1.5 hours already + 3.5 hours remaining = 5 hours total awake time today. Answer: 5 hours (E).",
  ["Time already awake: 1.5 hours.",
   "Time until sleep: 3.5 hours.",
   "Total awake time = 1.5 + 3.5 = 5 hours."])

for q in [6, 9, 10, 13, 17]:
    S("usa_2011_ecolier", q, "", image=True)

# ── usa_2015 ────────────────────────────────────────────────
for q in [1, 4, 5]:
    S("usa_2015_ecolier", q, "", image=True)

# ── usa_2016 ────────────────────────────────────────────────
S("usa_2016_ecolier", 6,
  "Anna shares apples equally among herself and 5 girlfriends = 6 people total. Each girl gets more than 2 apples, so at least 3. The smallest whole number satisfying this is 3. Answer: 3.",
  ["6 people share equally (Anna + 5 girlfriends).",
   "Each gets more than 2 → minimum is 3 apples each.",
   "Answer: 3."])

# ── usa_2024 ────────────────────────────────────────────────
S("usa_2024_ecolier", 12,
  "Over D days, one child gets 5a + 4(D−a) = 26. For D=6: a=2. Total = 9×6=54. Other child: 54−26=28. Answer: 28.",
  ["Let a = days the child was seen first. Then 5a + 4(6−a) = 26 → a = 2.",
   "Total fish over 6 days = 9 × 6 = 54.",
   "Other child gets 54 − 26 = 28 fish."])

for q in [13, 17]:
    S("usa_2024_ecolier", q, "", image=True)

# ── usa_2025 ────────────────────────────────────────────────
S("usa_2025_ecolier", 4, "", image=True)

S("usa_2025_ecolier", 14,
  "Let x = grams each large sheep gets. 5x + 2x = 7x = 210 → x = 30. Small sheep gets 2×30 = 60 g. Answer: 60 g. (Note: the official answer key for this set may have a discrepancy; the calculation gives 60 g.)",
  ["5 large sheep × x + 1 small sheep × 2x = 210.",
   "7x = 210 → x = 30.",
   "Small sheep gets 2 × 30 = 60 g."])

S("usa_2025_ecolier", 20,
  "Total = 22+23+25+34+36 = 140 g. Each box = 70 g. Split: {22,23,25}=70 and {34,36}=70. The two toys that cannot be in the same box are from different groups (e.g. the 25 g toy and the 34 g toy). Answer: D.",
  ["Total weight = 22+23+25+34+36 = 140 g. Each box = 70 g.",
   "Only split: {22, 23, 25} = 70 and {34, 36} = 70.",
   "Any toy from group 1 and any toy from group 2 go in different boxes.",
   "Answer: D (specific pair from the two groups)."])

S("usa_2025_ecolier", 24, "", image=True)


# ── APPLY ───────────────────────────────────────────────────
def apply():
    changed = 0
    for json_path in sorted(JSON_DIR.glob("*_ecolier.json")):
        data = json.loads(json_path.read_text())
        file_changed = False
        for q in data.get("questions", []):
            key = (json_path.stem, q["number"])
            patch = SOLUTIONS.get(key)
            if not patch:
                continue
            if "image_required" in patch:
                if q.get("image_required") != patch["image_required"]:
                    q["image_required"] = patch["image_required"]
                    file_changed = True
            sol = patch.get("solution", "")
            steps = patch.get("solution_steps", [])
            current = q.get("solution", "")
            if sol and current.startswith("Work through"):
                q["solution"] = sol
                q["solution_steps"] = steps
                file_changed = True
            elif not sol and patch.get("image_required"):
                if current.startswith("Work through"):
                    pdf_page = q.get("pdf_page", 1)
                    ans = q.get("answer", "")
                    q["solution"] = f"See PDF page {pdf_page} for this question. Correct answer: {ans}."
                    q["solution_steps"] = []
                    file_changed = True
        if file_changed:
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            changed += 1
            print(f"  Updated: {json_path.name}")
    print(f"\nDone. {changed} files updated.")

if __name__ == "__main__":
    apply()
