# Island Decoration PNG Assets

Drop generated decoration PNGs here. The frontend resolves each placed
decoration to `island/decor/{zone}_{slug}.png`. Missing files fall back to a
Lucide-icon placeholder badge tinted by `sub_category`, so partial coverage is
fine — start with whichever tier you generate first.

## File specs
- **Format:** PNG with transparent background (alpha channel required).
- **Size:** 256×256 px recommended (square). The UI scales to ~64–96 px.
- **Style:** Soft pastel, stationery feel. Match `bg_{zone}.png` lighting.
- **Background removal:** Use Photoroom / remove.bg if your generator outputs
  a solid background.

## Naming convention
`{zone}_{slug}.png` — lowercase, snake_case, no spaces. The canonical mapping
is the source of truth in `backend/migrations/023_island_decor_image_paths.py`.

## Required filenames (46 total)

### Forest (9)
- `forest_mushroom_lantern.png`
- `forest_signpost.png`
- `forest_honey_jar.png`
- `forest_cabin.png`
- `forest_fairy_gate.png`
- `forest_treehouse.png`
- `forest_firefly.png`
- `forest_flower_rain.png`
- `forest_mist.png`

### Ocean (9)
- `ocean_treasure_chest.png`
- `ocean_shell_chime.png`
- `ocean_coral_lantern.png`
- `ocean_garden.png`
- `ocean_sea_cave.png`
- `ocean_palace.png`
- `ocean_bubbles.png`
- `ocean_light_pillar.png`
- `ocean_aurora.png`

### Savanna (9)
- `savanna_baobab.png`
- `savanna_pride_rock.png`
- `savanna_oasis.png`
- `savanna_waterfall.png`
- `savanna_cliff.png`
- `savanna_cave.png`
- `savanna_sunset.png`
- `savanna_migration.png`
- `savanna_starry_sky.png`

### Space (9)
- `space_meteorite.png`
- `space_crater.png`
- `space_nebula.png`
- `space_black_hole.png`
- `space_asteroids.png`
- `space_star_cloud.png`
- `space_meteor_shower.png`
- `space_aurora.png`
- `space_wormhole.png`

### Legend (10)
- `legend_dragon_nest.png`
- `legend_rainbow_bridge.png`
- `legend_phoenix_tree.png`
- `legend_gumiho_shrine.png`
- `legend_qilin_prints.png`
- `legend_sacred_tree.png`
- `legend_magic_circle.png`
- `legend_golden_aura.png`
- `legend_rainbow_waterfall.png`
- `legend_star_altar.png`

## Validating coverage
From the repo root:

```bash
python3 scripts/check_decor_assets.py
```

Prints which slugs have a PNG and which are still missing. Exit code is `0`
when everything is present, `1` otherwise — handy for CI later.

## Where filenames are defined
- DB seed: `backend/migrations/023_island_decor_image_paths.py`
- Frontend resolver: `frontend/src/island/ZoneDetail.jsx` (`_zdDecorVisual`)
- Placeholder fallback: `<img onerror>` swap to Lucide icon box.
