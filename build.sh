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
  $JS/parent-panel.js \
  $JS/parent-overview.js \
  $JS/parent-goals.js \
  $JS/parent-textbooks.js \
  $JS/parent-math.js \
  $JS/parent-streak.js \
  $JS/parent-xp.js \
  $JS/parent-settings.js \
  $JS/parent-report.js \
  $JS/parent-ckla.js \
  $JS/parent-island.js \
  $JS/reward-shop.js \
  $JS/reward-shop-use.js \
  $JS/reward-shop-island.js \
  frontend/src/island/IslandMain.jsx \
  frontend/src/island/ZoneDetail.jsx \
  frontend/src/island/CharacterDetail.jsx \
  frontend/src/island/EvolutionModal.jsx \
  frontend/src/island/Onboarding.jsx \
  frontend/src/island/Inventory.jsx \
  frontend/src/island/Collection.jsx \
  frontend/src/island/LumiLog.jsx \
  frontend/src/island/IslandNotifications.jsx \
  frontend/src/island/FeedScreen.jsx \
  frontend/src/island/EmptyState.jsx \
  frontend/src/island/DailyScreen.jsx \
  frontend/src/island/SettingsScreen.jsx \
  frontend/src/island/PurchaseModal.jsx \
  frontend/src/island/LoadingScreen.jsx \
  frontend/src/island/ErrorScreen.jsx \
  frontend/src/island/Coachmarks.jsx \
  $JS/island-result.js \
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
  $JS/ckla-spelling.js \
  $JS/ckla-review.js \
  $JS/child.js \
  $JS/child-calendar.js \
  $JS/child-keyboard.js \
  $JS/child-text.js \
  $JS/sentence_ai.js \
  $JS/collocation.js \
  $JS/finaltest.js \
  $JS/unittest.js \
  $JS/review.js \
  $JS/review-hub.js \
  $JS/math-spaced-review.js \
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
  $JS/math-lesson-complete.js \
  $JS/math-unit-test.js \
  $JS/math-problems-ui.js \
  $JS/math-review.js \
  $JS/math-academy-submit.js \
  $JS/math-academy.js \
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
  $JS/arcade-word-builder.js \
  $JS/arcade-memory-match.js \
  | npx esbuild --minify --legal-comments=none --loader=js > $OUT/bundle-c.min.js
echo "  bundle-c.min.js done ($(wc -c < $OUT/bundle-c.min.js) bytes)"

# ─── Cache-bust child.html ──────────────────────────────────────────────
# Compute a single build hash from the freshly built bundles + every CSS
# file. Then rewrite every "?v=..." in child.html to that hash so a single
# server restart invalidates stale browser / service-worker caches across
# the board. No more bumping per-file versions by hand.
HTML="frontend/templates/child.html"
if [ -f "$HTML" ]; then
  BUILD_ID=$(cat \
    $OUT/bundle-a.min.js $OUT/bundle-b.min.js $OUT/bundle-c.min.js \
    frontend/static/css/*.css \
    frontend/static/js/splash.js \
    frontend/static/js/sound.js \
    frontend/static/js/offline-indicator.js \
    frontend/static/js/toast.js \
    frontend/static/js/core.js \
    frontend/static/js/tts-client.js \
    frontend/static/js/analytics.js \
    frontend/static/js/navigation.js \
    | shasum | cut -c1-8)
  # BSD sed (macOS) and GNU sed (Linux) both accept `-i.bak` + cleanup.
  sed -i.bak -E "s/\?v=[A-Za-z0-9]+/?v=$BUILD_ID/g" "$HTML"
  rm -f "$HTML.bak"
  echo "  cache-bust applied: ?v=$BUILD_ID"
fi

echo "Done."
