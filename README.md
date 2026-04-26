# Prompt Builder — Krita Docker Plugin

An AI prompt builder with Danbooru-style tag selection, three-state pos/neg cycling, tag weights, **model-based prompt presets**, separate pos/neg presets, and hex palette challenges — running directly inside **Krita** as a dockable panel.

## Installation

### ZIP Import (Recommended)
1. In Krita: **Tools → Scripts → Import Python Plugin from File...**
2. Select `krita-prompt-builder.zip`
3. **Restart Krita**
4. Go to **Settings → Dockers → Prompt Builder**

### Manual Install
1. Copy `prompt_builder.desktop` and the `prompt_builder/` folder to your `pykrita/` directory:
   - **Windows:** `%APPDATA%\krita\pykrita\`
   - **macOS:** `~/Library/Application Support/krita/pykrita/`
   - **Linux:** `~/.local/share/krita/pykrita/`
2. **Restart Krita**
3. **Settings → Dockers → Prompt Builder**

## Features

### Three-State Tag Cycling
Click any chip to cycle: **off → positive → negative → off**

### Model-Based Prompt Presets
Select a model from the dropdown to auto-load the optimal prompt format:
- **SDXL Base** — `masterpiece, best quality, ultra-detailed...`
- **Illustrious XL** — WAI-optimized Danbooru tags (`masterpiece, best quality, amazing quality, very aesthetic, newest`)
- **Pony Diffusion** — Score-based system (`score_9, score_8_up, score_7_up...`)
- **Flux** — Photographic language (`photo-realistic, sharp focus...`)
- **Animagine XL** — Hybrid anime/realistic

Each model auto-includes its recommended **positive prefix**, **negative prompt defaults**, sampler, steps, and CFG scale.

### Tag Weights
**Scroll up/down** on output tokens to adjust weight (0.1–2.0). Format: `(tag:1.5)`

### Positive & Negative Presets (Separate!)
Save and load **independent** preset sets:
- **Pos Presets** — Save positive tag selections, weights, character, and model
- **Neg Presets** — Save negative tag selections and weights
- Both appear as clickable chips with × to delete

### Prompt Output
- **Positive display** — section-colored tokens with weight badges + auto `white background`
- **Negative display** — red-tinted tokens + model default negatives
- **Separate Copy** buttons

### Edit Mode
Add/remove sections/chips, toggle single/multi, pick colors from 12-color palette, export config.

### Hex Palette Challenge
10 curated color palettes. Click to lock. Shuffle to randomize.

### Utilities
- **Multi** — global multi-select override
- **Randomize** — random per section (respects `randomize` flag)
- **Clear** — clear selections
- **Reset** — full wipe

## Tag Sections (14 Categories)

Quality, Artist, Subject Count, Race, Eye Color, Eye Type, Chest, Figure, Hair Color, Inner Hair Color, Hair Length, Hair Texture, Bangs, Hair Arrangement, Hair Details, Expression, Eye/Face Details, Outfit Preset, Top, Bottom, Hosiery, Shoes, Neck, Wrists/Hands, Eyewear, Belt, Headwear, Background/Setting, Pose/Action, Style/Theme — **300+ tag chips total**

## File Structure

```
prompt_builder.desktop          # Krita manifest (top level!)
prompt_builder/
├── __init__.py                 # Extension entry point
├── prompt_builder.py           # Main UI (~1100 lines)
├── tag_data.py                 # Tags + model presets + hex palettes (~1650 lines)
└── README.md
```

Auto-created:
- `presets.json` — positive presets
- `neg_presets.json` — negative presets

## License

MIT
