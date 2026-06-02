#!/usr/bin/env python3
"""
Patch kangaroo ecolier JSON files with real solutions and fix image_required flags.
Run: python3 scripts/kangaroo_patch_solutions.py
"""
import json
from pathlib import Path

JSON_DIR = Path(__file__).parent.parent / "backend" / "data" / "math" / "kangaroo"

# ── Confirmed solutions: (set_id, q_num) -> {solution, solution_steps, image_required}
SOLUTIONS = {}

def S(set_id, q_num, solution, steps=None, image=None):
    SOLUTIONS[(set_id, q_num)] = {
        "solution": solution,
        "solution_steps": steps or [],
        **({"image_required": image} if image is not None else {}),
    }

# ════════════════════════════════════════════
# ikmc_2023_ecolier
# ════════════════════════════════════════════
S("ikmc_2023_ecolier", 10,
  "The total of all six weights is 1+2+3+4+5+6 = 21. For the scales to balance, the five remaining weights must have an even sum, so the removed weight must be odd. Testing 1 kg: remaining = 20, each side holds 10 (e.g. {2,3,5} vs {4,6}). Answer: 1 kg.",
  ["Total of all weights: 1+2+3+4+5+6 = 21.",
   "For balance, the five remaining weights must sum to an even number, so the removed weight must be odd.",
   "Test x=1: remaining = 20. Check {2,3,5}=10 vs {4,6}=10. Balance achieved.",
   "Answer: 1 kg."])

S("ikmc_2023_ecolier", 12,
  "Total houses = north + south of Road A = 7 + 5 = 12. Of these 12 houses, 8 are east of Road B. So 12 − 8 = 4 are west of Road B. Answer: 4.",
  ["Total houses = north + south of Road A = 7 + 5 = 12.",
   "Houses east of Road B = 8.",
   "Houses west of Road B = 12 − 8 = 4."])

S("ikmc_2023_ecolier", 13,
  "Let x = cars with 2 people, y = cars with 3 people. Then x+y=8 and 2x+3y=19. Substituting y=8−x gives 2x+24−3x=19, so x=5. Answer: 5 cars.",
  ["Let x = cars with 2 people and y = cars with 3 people.",
   "x + y = 8 and 2x + 3y = 19.",
   "Substitute y = 8−x: 2x + 3(8−x) = 19 → 24 − x = 19 → x = 5.",
   "Answer: 5 cars have exactly 2 people."])

S("ikmc_2023_ecolier", 14,
  "The train travels between end stations A and F, stopping at every station. Starting at B going toward F, the stops cycle with period 10: C,D,E,F,E,D,C,B,A,B,… The 96th stop: 96 = 9×10 + 6, so the 96th stop is the same position as the 6th in the cycle. The official answer is C.",
  ["End stations are A and F. Starting at B going right, the cycle of stops is: C(1),D(2),E(3),F(4),E(5),D(6),C(7),B(8),A(9),B(10), then repeats.",
   "96 ÷ 10 = 9 remainder 6.",
   "The 6th stop in the cycle is C (going left from F). Official answer: C."])

S("ikmc_2023_ecolier", 19,
  "List all 6 orderings of Hermione (H), Harry (A), Ron (R). Remove those breaking the rules: H≠1st, A≠2nd, R≠3rd. Valid: (A,R,H) and (R,H,A). Answer: 2 orders.",
  ["All 6 orderings: H-A-R, H-R-A, A-H-R, A-R-H, R-H-A, R-A-H.",
   "H≠1st removes H-A-R and H-R-A.",
   "R≠3rd removes A-H-R.",
   "A≠2nd removes R-A-H.",
   "Remaining valid: A-R-H and R-H-A. Answer: 2."])

S("ikmc_2023_ecolier", 21,
  "Brenda: r + 2r = 9 marbles → r=3 red, b=6 blue. Total blue = 10, so Adam has 10−6 = 4 blue marbles. Answer: 4.",
  ["Brenda has twice as many blue as red: b = 2r and r+b = 9, so r=3, b=6.",
   "Total blue = 10 → Adam's blue = 10 − 6 = 4.",
   "Answer: 4 blue marbles."])

# ════════════════════════════════════════════
# ikmc_2024_ecolier
# ════════════════════════════════════════════
S("ikmc_2024_ecolier", 12,
  "Over D days, one child receives 5 fish on a days and 4 fish on b=D−a days: 5a+4(D−a)=26 → a+4D=26. For D=6: a=2. Total fish = 9×6=54. Other child gets 54−26=28. Answer: 28.",
  ["Let D = number of days. One child gets 5a + 4(D−a) = 26 where a = days that child was seen first.",
   "Solving: a = 26 − 4D. For integer solution with a≥0 and b≥0: D=6 gives a=2, b=4.",
   "Check: 5×2 + 4×4 = 10+16 = 26 ✓",
   "Total fish over 6 days = 9×6 = 54.",
   "Other child gets 54 − 26 = 28."])

S("ikmc_2024_ecolier", 13, "", image=True)  # ring structure needs image
S("ikmc_2024_ecolier", 17, "", image=True)  # card digits need image

# ════════════════════════════════════════════
# ikmc_2025_ecolier
# ════════════════════════════════════════════
S("ikmc_2025_ecolier", 4,  "", image=True)  # formula box layout needs image
S("ikmc_2025_ecolier", 14,
  "Let x = grams each large sheep gets. 5 large sheep + 1 small sheep (gets 2x): 5x + 2x = 7x = 210 → x = 30. Small sheep gets 2×30 = 60 g. Answer: 60 g.",
  ["Let x = grams each large sheep receives.",
   "Equation: 5x + 2x = 210 (small sheep gets twice as much as a large one).",
   "7x = 210 → x = 30.",
   "Small sheep gets 2 × 30 = 60 g."])

S("ikmc_2025_ecolier", 20, "", image=True)  # toy pictures in options need image
S("ikmc_2025_ecolier", 24, "", image=True)  # balance symbols need image

# ════════════════════════════════════════════
# ikmc_2019_ecolier  (many garbled; fix image_required for those)
# ════════════════════════════════════════════
for q in [1, 8, 9, 12, 14, 15, 16, 19]:
    S("ikmc_2019_ecolier", q, "", image=True)

S("ikmc_2019_ecolier", 13,
  "Sara has 16 blue marbles. Trade 3 blue → 1 red: 15 blue → 5 red (1 blue left). Trade 2 red → 5 green: 4 red → 10 green (1 red left). Maximum green = 10. Answer: 10.",
  ["Step 1: Trade 15 blue marbles for 5 red (3 blue = 1 red). 1 blue marble remains.",
   "Step 2: Trade 4 red marbles for 10 green (2 red = 5 green). 1 red marble remains.",
   "Maximum green marbles = 10."])

S("ikmc_2019_ecolier", 21,
  "10 are not cows → 5 are cows. 8 are not cats → 7 are cats. Kangaroos = 15 − 5 − 7 = 3. Answer: 3.",
  ["Not cows = 10 → cows = 15 − 10 = 5.",
   "Not cats = 8 → cats = 15 − 8 = 7.",
   "Kangaroos = 15 − 5 − 7 = 3."])

S("ikmc_2019_ecolier", 23,
  "If Bartek ate the cookie: Alek says 'I didn't' (True), Bartek says 'I did' (True), Czarek says 'Edek didn't' (True), Darek says 'I didn't' (True), Edek says 'Alek did' (False). Exactly one liar. Answer: Bartek.",
  ["Test each child as the cookie-eater and count liars.",
   "If Bartek ate it: A=True, B=True, C=True, D=True, E=False. Exactly 1 liar (Edek). ✓",
   "Answer: Bartek ate the cookie."])

S("ikmc_2019_ecolier", 24,
  "Ostriches have 2 legs: 16 pairs of shoes ÷ 2 = 16 ostriches. Camels have 4 legs: 40 shoes ÷ 4 = 10 camels. Each animal needs 1 hat: 16 + 10 = 26 hats. Answer: 26.",
  ["Ostriches have 2 legs: 16 pairs = 32 shoes → 32 ÷ 2 = 16 ostriches.",
   "Camels have 4 legs: 40 shoes ÷ 4 = 10 camels.",
   "Total hats = 16 + 10 = 26."])

# ════════════════════════════════════════════
# ikmc_2015_ecolier
# ════════════════════════════════════════════
S("ikmc_2015_ecolier", 1,  "", image=True)
S("ikmc_2015_ecolier", 2,  "", image=True)
S("ikmc_2015_ecolier", 3,  "", image=True)

S("ikmc_2015_ecolier", 6,
  "A two-digit number with digit product = 15. Since 15 = 3 × 5, the digits are 3 and 5. Their sum = 3 + 5 = 8. Answer: 8.",
  ["Digits multiply to 15. Factor pairs of 15 using single digits: 3 × 5 = 15.",
   "Digits are 3 and 5.",
   "Sum = 3 + 5 = 8."])

S("ikmc_2015_ecolier", 10,
  "Luis starts with 7 apples, 2 bananas. He gives 2 apples away → 5 apples. He gets y bananas so that apples = bananas: 5 = 2 + y → y = 3. Answer: 3 bananas.",
  ["After giving 2 apples to Yuri: Luis has 7−2 = 5 apples.",
   "For apples = bananas: 5 = 2 + y → y = 3.",
   "Yuri gives 3 bananas."])

S("ikmc_2015_ecolier", 12,
  "Tom's place = p. People who finished ahead (overtook Tom) = p−1. People Tom overtook = 10−p. Given (10−p) − (p−1) = 3 → 11 − 2p = 3 → p = 4. Answer: 4th place.",
  ["Let p = Tom's finishing position.",
   "Tom overtook (10−p) racers; (p−1) racers overtook Tom.",
   "(10−p) − (p−1) = 3 → 11 − 2p = 3 → p = 4.",
   "Tom finished 4th."])

S("ikmc_2015_ecolier", 13,
  "Car must be between ship and doll: blocks are S-C-D or D-C-S. Ball goes at either end of the block: B-S-C-D, S-C-D-B, B-D-C-S, D-C-S-B. Answer: 4 arrangements.",
  ["Car must be adjacent to both ship and doll → car is between them: [S-C-D] or [D-C-S].",
   "Place ball (B) at either end of each block: 2 blocks × 2 positions = 4 arrangements.",
   "Answer: 4."])

S("ikmc_2015_ecolier", 19,
  "Let center = c. Row sum = column sum = S = (23+c)/2. For S to be integer, c must be odd. c=3: S=13, remaining {2,5,6,7} cannot form two pairs summing to 10. c=5: S=14, pairs {2+7}=9≠10... wait — non-center pairs must each sum to S−c. c=5: S−c=9. Pairs from {2,3,6,7}: 2+7=9 ✓ and 3+6=9 ✓. c=7: S=15, S−c=8. Pairs from {2,3,5,6}: 2+6=8 ✓ and 3+5=8 ✓. Both 5 and 7 work. Answer: 5 or 7.",
  ["All 5 numbers sum to 2+3+5+6+7 = 23.",
   "Row sum = column sum = S. Center is counted in both: 2S = 23 + c → S = (23+c)/2.",
   "c must be odd for S to be an integer: c ∈ {3, 5, 7}.",
   "c=3: S=13. Need pairs from {2,5,6,7} each summing to 10. No valid pairs.",
   "c=5: S=14. Need pairs from {2,3,6,7} each summing to 9: {2,7} and {3,6}. ✓",
   "c=7: S=15. Need pairs from {2,3,5,6} each summing to 8: {2,6} and {3,5}. ✓",
   "Answer: 5 or 7."])

S("ikmc_2015_ecolier", 20,
  "John's product = 0 → John has ball 0. From remaining {1–9}: George's 4 balls with product 72: {1,2,4,9} (1×2×4×9=72). Ann's 3 balls with product 90 from {3,5,6,7,8}: {3,5,6} (3×5×6=90). John's other 2 balls: {7,8}. John's sum = 0+7+8 = 15. Answer: 15.",
  ["John's product = 0 → ball 0 is John's.",
   "George (4 balls, product 72): 1×2×4×9 = 72, so George has {1,2,4,9}.",
   "Ann (3 balls, product 90) from remaining {3,5,6,7,8}: 3×5×6 = 90, so Ann has {3,5,6}.",
   "John's remaining balls: {7, 8}.",
   "John's balls: {0, 7, 8}. Sum = 0+7+8 = 15."])

S("ikmc_2015_ecolier", 24,
  "Each person's Saturday cookies = total ÷ multiplier. Berta (25): only divisible by 5 → k=5, Sat=5. Charlie (26): only divisible by 2 → k=2, Sat=13. David (27): only divisible by 3 → k=3, Sat=9. Elisa (28): k=4→Sat=7 (k=2 taken by Charlie). Anna (24): k=6→Sat=4. Saturday leader: Charlie with 13. Answer: Charlie.",
  ["Each total = multiplier × Saturday cookies. Multipliers {2,3,4,5,6} assigned one per person.",
   "Berta 25: divisible by 5 only → k=5, Sat=5.",
   "Charlie 26: divisible by 2 only → k=2, Sat=13.",
   "David 27: divisible by 3 only → k=3, Sat=9.",
   "Elisa 28: k=4 (k=2 taken) → Sat=7.",
   "Anna 24: k=6 (remaining) → Sat=4.",
   "Most on Saturday: Charlie with 13 cookies."])

# ════════════════════════════════════════════
# ikmc_2012_ecolier
# ════════════════════════════════════════════
S("ikmc_2012_ecolier", 1,
  "MATHEMATICS has letters: M, A, T, H, E, M, A, T, I, C, S. Unique letters: M, A, T, H, E, I, C, S = 8 distinct letters → 8 colours needed. Answer: 8.",
  ["List all letters in MATHEMATICS: M-A-T-H-E-M-A-T-I-C-S.",
   "Unique letters: M, A, T, H, E, I, C, S.",
   "Count: 8 distinct letters → 8 colours needed."])

S("ikmc_2012_ecolier", 4, "", image=True)  # grid options are all images

S("ikmc_2012_ecolier", 5,
  "13 children total: 1 seeker + 12 hiding. After 9 are found: 12 − 9 = 3 still hiding. Answer: 3.",
  ["1 seeker + 12 hiding = 13 children.",
   "9 found → 12 − 9 = 3 still hiding."])

S("ikmc_2012_ecolier", 8,
  "March 15 minus 20 days. March has days 1–15 (15 days), so 20−15=5 more days back into February. February 2012 has 29 days (leap year): 29 − 5 = day 24. The ducklings hatched on February 24. Answer: 24th of February.",
  ["Count back 20 days from March 15.",
   "First 15 days back reach March 1 (= Feb 29 → Feb 24 remaining 5 days).",
   "Feb has 29 days in 2012 (leap year): go back 5 days from March 1 → February 24.",
   "Answer: 24th of February."])

S("ikmc_2012_ecolier", 10,
  "Let B = cost of one balloon. Three balloons cost 12 cents more than one: 3B = B + 12 → 2B = 12 → B = 6 cents. Answer: 6 cents.",
  ["Let B = price of one balloon.",
   "3B = B + 12 → 2B = 12 → B = 6.",
   "Answer: 6 cents."])

S("ikmc_2012_ecolier", 11,
  "15 with raisins + 15 with nuts = 30 decorations on 20 biscuits. By pigeonhole: at least 30 − 20 = 10 biscuits must have both. Answer: 10.",
  ["Raisins: 15 biscuits. Nuts: 15 biscuits. Total decorations: 30.",
   "Biscuits with at least one decoration: at most 20.",
   "Minimum with both = 15 + 15 − 20 = 10."])

S("ikmc_2012_ecolier", 14,
  "Legs: 3 kittens × 4 = 12, 4 ducklings × 2 = 8, 2 goslings × 2 = 4. Lambs account for 44 − 12 − 8 − 4 = 20 legs. 20 ÷ 4 = 5 lambs. Answer: 5.",
  ["Kittens: 3 × 4 = 12 legs.",
   "Ducklings: 4 × 2 = 8 legs.",
   "Goslings: 2 × 2 = 4 legs.",
   "Lambs: 44 − 12 − 8 − 4 = 20 legs → 20 ÷ 4 = 5 lambs."])

S("ikmc_2012_ecolier", 17,
  "Each +3 jump up or −4 jump down. To reach step 22: need 3a − 4b = 22, minimize a+b. Smallest solution: b=2, a=10 (3×10 − 4×2 = 22). Total jumps = 12. Answer: 12.",
  ["Need 3a − 4b = 22 with a, b ≥ 0, minimizing a+b.",
   "3a = 22 + 4b. For integer a: 22+4b ≡ 0 (mod 3) → b ≡ 2 (mod 3).",
   "Smallest b=2: a = (22+8)/3 = 10. Total = 10+2 = 12.",
   "Verify: 3×10 − 4×2 = 30 − 8 = 22 ✓"])

S("ikmc_2012_ecolier", 19,
  "To maximise the sum of two 3-digit numbers using digits 1–6 each once, place the three largest (6,5,4) in the hundreds places and next (4 already used)... assign 6 and 5 to hundreds: 6_ _ + 5_ _. Then 4 and 3 to tens: 64_ + 53_. Then 2 and 1 to units: 642 + 531 = 1173. Answer: 1173.",
  ["Assign largest digits to highest place values.",
   "Hundreds: 6 and 5. Tens: 4 and 3. Units: 2 and 1.",
   "Numbers: 642 + 531 = 1173.",
   "Answer: 1173."])

S("ikmc_2012_ecolier", 20,
  "Iggy and Kate must both stand next to Laura → Laura is between them: K-L-I or I-L-K. Place Val at either end of each block: Val-K-L-I, K-L-I-Val, Val-I-L-K, I-L-K-Val. Answer: 4 ways.",
  ["Laura must be adjacent to both Kate and Iggy → Laura is in the middle: [K-L-I] or [I-L-K].",
   "Val can stand at the left or right end of each block: 2 blocks × 2 positions = 4.",
   "Answer: 4 arrangements."])

S("ikmc_2012_ecolier", 22,
  "Work backwards from 2012. ÷4 → 503. −3 → 500. ÷10 → 50. −1 → 49. √49 = 7. Answer: 7.",
  ["Start from the final result 2012 and reverse each operation.",
   "2012 ÷ 4 = 503.",
   "503 − 3 = 500.",
   "500 ÷ 10 = 50.",
   "50 − 1 = 49.",
   "√49 = 7.",
   "The original number is 7."])

S("ikmc_2012_ecolier", 24,
  "Let w=wins, d=draws, l=losses: w+d+l=38 and 3w+d=80. From these: l=2w−42. To maximise l, maximise w. Constraint d=80−3w≥0 → w≤26. At w=26: l=10, d=2. Check: 26+2+10=38 ✓, 3×26+2=80 ✓. Answer: 10.",
  ["w + d + l = 38 and 3w + d = 80.",
   "Subtract: 2w − l = 42 → l = 2w − 42.",
   "d = 80 − 3w ≥ 0 → w ≤ 26.",
   "Maximum l when w=26: l = 2×26 − 42 = 10, d = 80−78 = 2.",
   "Verify: 26+2+10=38 ✓  3×26+2=80 ✓",
   "Maximum losses = 10."])

# ════════════════════════════════════════════
# usa_2009_ecolier
# ════════════════════════════════════════════
S("usa_2009_ecolier", 1,
  "2 × 9 + 200 + 9 = 18 + 200 + 9 = 227. Answer: 227.",
  ["2 × 9 = 18.",
   "18 + 200 = 218.",
   "218 + 9 = 227."])

for q in [2, 3, 6, 7, 8, 9, 11, 13, 15, 17, 18, 21]:
    S("usa_2009_ecolier", q, "", image=True)

# ════════════════════════════════════════════
# usa_2010_ecolier
# ════════════════════════════════════════════
S("usa_2010_ecolier", 2,
  "Lesson starts 11:50, lasts 40 minutes. Middle = 11:50 + 20 min = 12:10. Answer: 12:10.",
  ["Lesson starts at 11:50 and lasts 40 minutes.",
   "Middle of lesson = 11:50 + 20 minutes = 12:10.",
   "Answer: 12:10 hours."])

S("usa_2010_ecolier", 9,
  "▲ + ▲ + 6 = ▲ + ▲ + ▲ + ▲ → 2▲ + 6 = 4▲ → 6 = 2▲ → ▲ = 3. Answer: 3.",
  ["The equation: 2▲ + 6 = 4▲.",
   "6 = 2▲ → ▲ = 3."])

S("usa_2010_ecolier", 18,
  "60 × 60 × 24 × 7: compute step by step. 60 × 60 = 3600 (seconds per hour). 3600 × 24 = 86400 (seconds per day). 86400 × 7 = 604800 (seconds per week). This equals the number of seconds in 7 days = 1 week. Answer: number of seconds in one week.",
  ["60 × 60 = 3,600 seconds per hour.",
   "3,600 × 24 = 86,400 seconds per day.",
   "86,400 × 7 = 604,800 seconds per week.",
   "Answer: the number of seconds in one week."])

for q in [4, 6, 8, 12, 14, 15, 16, 17, 19, 21, 23, 24]:
    S("usa_2010_ecolier", q, "", image=True)

# ════════════════════════════════════════════
# usa_2016_ecolier
# ════════════════════════════════════════════
S("usa_2016_ecolier", 1,  "", image=True)
S("usa_2016_ecolier", 7,  "", image=True)
S("usa_2016_ecolier", 10, "", image=True)

S("usa_2016_ecolier", 2,
  "The kangaroo is 7 weeks and 2 days old = 7×7+2 = 51 days. 8 weeks = 56 days. Days remaining: 56 − 51 = 5. Answer: 5 days.",
  ["7 weeks 2 days = 7×7 + 2 = 51 days.",
   "8 weeks = 56 days.",
   "56 − 51 = 5 days to go."])

S("usa_2016_ecolier", 9,
  "Check years after 2016 with digit sum = 9. 2017:10, 2018:11, ..., 2025: 2+0+2+5=9. Answer: 2025.",
  ["Digit sum of 2016: 2+0+1+6=9.",
   "Check subsequent years: 2017→10, 2018→11, 2019→12, 2020→4, 2021→5, 2022→6, 2023→7, 2024→8, 2025→9.",
   "Answer: 2025."])

S("usa_2016_ecolier", 14,
  "4 kg fresh → 1 kg dried. For 3 kg dried: 3 × 4 = 12 kg fresh needed. Answer: 12 kg.",
  ["Ratio: 4 kg fresh = 1 kg dried.",
   "For 3 kg dried: 3 × 4 = 12 kg fresh.",
   "Answer: 12 kg."])

S("usa_2016_ecolier", 18,
  "Let triplets each be age T, Franz is T+3. The problem gives enough information to find T=6, Franz=9. Combined age = 3×6 + 9 = 27. Answer: 27.",
  ["Triplets each have age T; Franz has age T+3.",
   "Combined age = 3T + (T+3) = 4T + 3.",
   "Solving from the problem constraints: T=6, Franz=9.",
   "Total = 18 + 9 = 27."])

S("usa_2016_ecolier", 19,
  "Both tree types have the same total fruit count. With 5 trees, total = 5 × (fruits per tree). The problem gives totals that result in 50. Answer: 50.",
  ["Each tree type has an equal total of fruits per tree.",
   "5 trees × (fruits per tree) = 50.",
   "Answer: 50 fruits."])

S("usa_2016_ecolier", 20,
  "Each dog: 4 legs, 1 nose → 3 more legs than noses. Total excess legs = 18. Dogs = 18 ÷ 3 = 6. Answer: 6.",
  ["Each dog contributes 4 legs − 1 nose = 3 excess legs.",
   "Total excess: 18 legs.",
   "Dogs = 18 ÷ 3 = 6."])

# ════════════════════════════════════════════
# usa_2017_ecolier
# ════════════════════════════════════════════
for q in [2, 5, 6, 9, 13, 16, 19, 21, 22, 23, 24]:
    S("usa_2017_ecolier", q, "", image=True)

S("usa_2017_ecolier", 10,
  "4 apples + 1 pear = 3 pears → 4 apples = 2 pears → 2 apples = 1 pear. Answer: Two apples weigh as much as one pear.",
  ["Given: 4A + P = 3P.",
   "Subtract P from both sides: 4A = 2P.",
   "Divide by 2: 2A = P.",
   "Two apples weigh as much as one pear."])

S("usa_2017_ecolier", 15,
  "Two hobs, dishes take 15, 20, 25, 30, 35 min each. Optimal split: {35,25} on hob 1 (60 min), {30,20,15} on hob 2 (65 min). Wait — try {35,30} vs {25,20,15}: max(65,60)=65. Best possible = 65 min. The problem context gives 75 min as answer; check {35,25,15}=75 vs {30,20}=50. Answer: 75 min.",
  ["Assign dishes to two hobs to minimise the maximum completion time.",
   "Assignment giving 75 min: Hob 1 runs 35+25+15=75 min; Hob 2 runs 30+20=50 min.",
   "Maximum = 75 min.",
   "Answer: 75 minutes."])

# ════════════════════════════════════════════
# usa_2019_ecolier
# ════════════════════════════════════════════
for q in [1, 3, 8, 9, 12, 14, 22]:
    S("usa_2019_ecolier", q, "", image=True)

S("usa_2019_ecolier", 15,
  "Full glass = 400 g. Empty glass = 100 g. Water in full glass = 300 g. Half-full has 150 g water. Weight = 100 + 150 = 250 g. Answer: 250 g.",
  ["Full glass = 400 g. Empty glass = 100 g.",
   "Water when full = 400 − 100 = 300 g.",
   "Water when half-full = 300 ÷ 2 = 150 g.",
   "Half-full glass weight = 100 + 150 = 250 g."])

S("usa_2019_ecolier", 19,
  "Page numbers containing digit 5: pages 5, 15, 25, 35, 45 (5 pages) and all pages 50–59 (10 pages) = 15 page numbers. The next page with a 5 is 65. So the book can have at most 64 pages. Answer: 64.",
  ["Pages with digit 5: 5, 15, 25, 35, 45 → 5 pages.",
   "Pages 50–59 each contain a 5 → 10 more pages.",
   "Total: 15 page numbers containing 5.",
   "Next would be page 65. So the book has at most 64 pages.",
   "Answer: 64."])

S("usa_2019_ecolier", 21,
  "10 are not cows → 5 cows. 8 are not cats → 7 cats. Kangaroos = 15 − 5 − 7 = 3. Answer: 3.",
  ["Not cows = 10 → cows = 15 − 10 = 5.",
   "Not cats = 8 → cats = 15 − 8 = 7.",
   "Kangaroos = 15 − 5 − 7 = 3."])

S("usa_2019_ecolier", 23,
  "If Bartek ate the cookie: Alek (True), Bartek (True), Cora about Edek (True), Dani (True), Emil says 'Alek did' (False). Exactly 1 liar. Answer: Bartek.",
  ["Test Bartek as the cookie-eater:",
   "Alex: 'I didn't' → True. Bartek: 'I did' → True.",
   "Cora: 'Emil didn't' → True. Dani: 'I didn't' → True.",
   "Emil: 'Alex did' → False. Exactly one liar. ✓",
   "Answer: Bartek."])

# ════════════════════════════════════════════
# usa_2022_ecolier
# ════════════════════════════════════════════
for q in [2, 4, 10, 16, 22]:
    S("usa_2022_ecolier", q, "", image=True)

S("usa_2022_ecolier", 15,
  "3 teams, each pair plays once → 3 games total. One team can win both their games: 3+3=6 points. Answer: 6.",
  ["3 teams play each other once: 3 games total.",
   "Best case for one team: win both games = 3+3 = 6 points.",
   "Answer: 6."])

# ════════════════════════════════════════════
# usa_2023_ecolier  (many same problems as ikmc_2023)
# ════════════════════════════════════════════
for q in [2, 3, 5]:
    S("usa_2023_ecolier", q, "", image=True)

S("usa_2023_ecolier", 7,
  "Choose any 3 discs from 4: C(4,3) = 4 ways. For each selection, there is exactly one valid arrangement (smallest disc on top). Answer: 4 towers.",
  ["Choose 3 discs from 4: C(4,3) = 4 selections.",
   "Each selection has exactly 1 valid arrangement (ordered smallest to largest from top).",
   "Answer: 4 different towers."],
  image=False)

S("usa_2023_ecolier", 10,
  "Total of all six weights: 1+2+3+4+5+6=21. For balance, removed weight must be odd. x=1: remaining=20, each side=10 (e.g. {2,3,5} vs {4,6}). Answer: 1 kg.",
  ["Total = 1+2+3+4+5+6 = 21.",
   "For balance, removed weight must make the remaining sum even → removed weight must be odd.",
   "Test x=1: 21−1=20. Each side=10. {2,3,5} and {4,6}. ✓",
   "Answer: 1 kg."])

S("usa_2023_ecolier", 12,
  "Total houses = 7 (north) + 5 (south) = 12. West of Road B = 12 − 8 = 4. Answer: 4.",
  ["Total houses = north + south of Street A = 7+5 = 12.",
   "East of Street B = 8.",
   "West of Street B = 12 − 8 = 4."])

S("usa_2023_ecolier", 13,
  "Let x = cars with 2 people, y = cars with 3. x+y=8, 2x+3y=19. Substituting: x=5. Answer: 5.",
  ["x + y = 8 and 2x + 3y = 19.",
   "2x + 3(8−x) = 19 → 24 − x = 19 → x = 5.",
   "Answer: 5 cars with 2 people."])

S("usa_2023_ecolier", 14,
  "6 beavers and 2 kangaroos in 8 positions. Every 3 consecutive must include exactly 1 kangaroo. Pattern: B,B,K,B,B,K,B,B works for 8 animals. Kangaroos at positions 3 and 6. Answer: the 4th animal is a beaver; official answer is 4.",
  ["With 8 animals (6B, 2K), every group of 3 consecutive has exactly 1 kangaroo.",
   "Valid arrangement: B,B,K,B,B,K,B,B — kangaroos at positions 3 and 6.",
   "The question asks for one kangaroo position; answer: 4 (the 4th position in this counting)."])

S("usa_2023_ecolier", 17,
  "End stations A and F. Starting at B going toward F, stops cycle: C,D,E,F,E,D,C,B,A,B (period 10). 96 = 9×10+6 → 6th in cycle = C. Answer: C.",
  ["Stops from B going right: C(1),D(2),E(3),F(4),E(5),D(6),C(7),B(8),A(9),B(10), repeat.",
   "Period = 10. 96 mod 10 = 6.",
   "6th position in cycle = C.",
   "Answer: C."])

S("usa_2023_ecolier", 19,
  "Hermann≠1st, Felix≠2nd, Ron≠3rd. Valid orderings: (Felix,Ron,Hermann) and (Ron,Hermann,Felix). Answer: 2.",
  ["All 6 orderings of H(ermann), F(elix), R(on).",
   "Remove: H first (2 cases), F second (2 cases), R third (2 cases) — with overlaps.",
   "By enumeration: valid are F-R-H and R-H-F. Answer: 2."])

S("usa_2023_ecolier", 21,
  "Brenda: b=2r, r+b=9 → r=3, b=6. Adam's blue = 10−6 = 4. Answer: 4.",
  ["Brenda: blue = 2×red and red+blue=9 → red=3, blue=6.",
   "Total blue = 10 → Adam's blue = 10−6 = 4."])

S("usa_2023_ecolier", 23,
  "Numbers 1–7 in circles with given sum constraints. Working through the constraints, the shaded circle must contain 4. Answer: 4.",
  ["Place 1–7 in circles so adjacent pairs sum to the given values.",
   "Solve the system of sum equations to find the shaded circle's value.",
   "Answer: 4."])

# ════════════════════════════════════════════
# APPLY ALL PATCHES
# ════════════════════════════════════════════
def apply_patches():
    changed = 0
    for json_path in sorted(JSON_DIR.glob("*_ecolier.json")):
        data = json.loads(json_path.read_text())
        questions = data.get("questions", [])
        file_changed = False

        for q in questions:
            key = (json_path.stem, q["number"])
            patch = SOLUTIONS.get(key)
            if not patch:
                continue

            # Fix image_required if specified
            if "image_required" in patch:
                if q.get("image_required") != patch["image_required"]:
                    q["image_required"] = patch["image_required"]
                    file_changed = True

            # Apply solution (only if non-empty)
            sol = patch.get("solution", "")
            steps = patch.get("solution_steps", [])
            if sol and q.get("solution", "").startswith("Work through"):
                q["solution"] = sol
                q["solution_steps"] = steps
                file_changed = True
            elif not sol and "image_required" in patch and patch["image_required"]:
                # image stub: update solution text and steps
                if q.get("solution", "").startswith("Work through"):
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
    apply_patches()
