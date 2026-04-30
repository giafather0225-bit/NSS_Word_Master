#!/bin/bash
# build.sh — Bundle and minify deferred JS into 3 files
# Run: bash build.sh
set -e
cd "$(dirname "$0")"
JS=frontend/static/js
OUT=$JS

echo "Building JS bundles..."

# Bundle A: feature modules (pre-katex)
cat \
  $JS/preview.js \
  $JS/wordmatch.js \
  $JS/fillblank.js \
  $JS/spelling.js \
  $JS/sentence.js \
  $JS/home.js \
  $JS/growth-theme.js \
  $JS/parent-panel.js \
  $JS/parent-overview.js \
  $JS/parent-goals.js \
  $JS/parent-textbooks.js \
  $JS/parent-math.js \
  $JS/parent-streak.js \
  $JS/parent-xp.js \
  $JS/parent-settings.js \
  $JS/parent-report.js \
  $JS/reward-shop.js \
  $JS/reward-shop-use.js \
  $JS/reward-shop-island.js \
  frontend/src/island/IslandMain.jsx \
  frontend/src/island/ZoneDetail.jsx \
  frontend/src/island/CharacterDetail.jsx \
  frontend/src/island/EvolutionModal.jsx \
  frontend/src/island/Onboarding.jsx \
  frontend/src/island/IslandShop.jsx \
  frontend/src/island/Inventory.jsx \
  frontend/src/island/Collection.jsx \
  $JS/diary.js \
  $JS/diary-home.js \
  $JS/diary-write.js \
  $JS/diary-entry.js \
  $JS/diary-calendar.js \
  $JS/free-writing.js \
  $JS/calendar.js \
  $JS/daily-words.js \
  $JS/daily-words-weekly.js \
  $JS/ckla.js \
  $JS/ckla-lesson.js \
  $JS/ckla-review.js \
  $JS/child.js \
  $JS/child-calendar.js \
  $JS/child-keyboard.js \
  $JS/child-text.js \
  $JS/child-exam.js \
  $JS/sentence_ai.js \
  $JS/collocation.js \
  $JS/finaltest.js \
  $JS/unittest.js \
  $JS/review.js \
  | npx esbuild --minify --legal-comments=none --loader=js > $OUT/bundle-a.min.js
echo "  bundle-a.min.js done ($(wc -c < $OUT/bundle-a.min.js) bytes)"

# Bundle B: math modules (post-katex — depends on katex CDN)
cat \
  $JS/math-katex-utils.js \
  $JS/math-manipulatives.js \
  $JS/math-manipulatives-2.js \
  $JS/math-3read.js \
  $JS/math-problem-types.js \
  $JS/math-problem-ui.js \
  $JS/math-learn-visuals.js \
  $JS/math-learn-cards.js \
  $JS/math-academy-ui.js \
  $JS/math-academy-shell.js \
  $JS/math-academy-feedback.js \
  $JS/math-academy.js \
  $JS/math-review.js \
  $JS/math-fluency.js \
  $JS/math-placement.js \
  $JS/math-placement-results.js \
  $JS/math-daily.js \
  $JS/math-kangaroo.js \
  $JS/math-kangaroo-exam.js \
  $JS/math-kangaroo-pdf-exam.js \
  $JS/math-kangaroo-result.js \
  $JS/math-glossary.js \
  $JS/math-navigation.js \
  | npx esbuild --minify --legal-comments=none --loader=js > $OUT/bundle-b.min.js
echo "  bundle-b.min.js done ($(wc -c < $OUT/bundle-b.min.js) bytes)"

# Bundle C: word-manager + arcade
cat \
  $JS/word-manager.js \
  $JS/arcade-sfx.js \
  $JS/arcade.js \
  $JS/arcade-word-invaders.js \
  $JS/arcade-definition-match.js \
  $JS/arcade-spell-rush.js \
  $JS/arcade-crossword.js \
  $JS/arcade-math-invaders.js \
  $JS/arcade-sudoku.js \
  $JS/arcade-make24.js \
  | npx esbuild --minify --legal-comments=none --loader=js > $OUT/bundle-c.min.js
echo "  bundle-c.min.js done ($(wc -c < $OUT/bundle-c.min.js) bytes)"

echo "Done."
