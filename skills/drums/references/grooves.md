# Drum groove starting points

The BPM ranges, swings and patterns below are adaptable sketches, not transcriptions or genre definitions. Each example is a complete four-bar 4/4 MIDI spec. All use voices supported by built-in `drum_synth` and set `drum_map` to `soundcraft`; this is a custom map, not GM. A different map requires a compatible verified instrument. Save a spec in the user's workspace with a fresh output name, then run commands from the drums skill directory: `python ../soundcraft-core/scripts/make_midi.py "/absolute/work/groove.json" --json`. Step strings use `x` normal, `X` accent, `g` ghost, and `.` rest. Humanize is light and seeded. Fills occur every four bars and replace only the listed voice.

## pop

**BPM:** 100–125; example 112. **Swing:** 0.50, straight eighths. **Main:** kick on 1 and 3, snare on 2 and 4, even hats. **Variation:** add a kick pickup late in the bar. **Fill:** a one-bar snare/tom lift at bar 4; keep room for the vocal.

```json
{
  "bpm": 112, "time_signature": [4, 4], "output": "pop-drums.mid",
  "tracks": [{"name": "Pop Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.03, "seed": 21,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx"}}, "drum_map": "soundcraft"}]
}
```

## Thai pop/Luk thung

**BPM:** 90–130; example 108. **Swing:** 0.52. **Main:** steady kick/snare with lightly syncopated hats. **Variation:** open the hat at a phrase edge. **Fill:** compact tom/snare turn at bar 4. This is a pop-oriented MIDI sketch, not a claim of traditional Luk thung instrumentation; use a specific recording/reference for idiomatic detail.

```json
{
  "bpm": 108, "time_signature": [4, 4], "output": "thai-pop-drums.mid",
  "tracks": [{"name": "Thai Pop Drums", "type": "drums", "steps": 16, "swing": 0.52, "bars": 4, "humanize": 0.03, "seed": 22,
    "pattern": {"kick": "x...x..x....x...", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x.", "open_hat": "..............x."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx", "tom_hi": "............x.x."}}, "drum_map": "soundcraft"}]
}
```

## ballad

**BPM:** 60–85; example 72. **Swing:** 0.50. **Main:** spacious kick and backbeat with gentle cymbal timekeeping. **Variation:** omit a kick to open a vocal phrase. **Fill:** soft tom approach into the next section; avoid busy subdivisions.

```json
{
  "bpm": 72, "time_signature": [4, 4], "output": "ballad-drums.mid",
  "tracks": [{"name": "Ballad Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 23,
    "pattern": {"kick": "x.......x.......", "snare": "........x.......", "ride": "x...x...x...x..."},
    "fill": {"every": 4, "pattern": {"tom_low": "............x...", "snare": ".............g.x"}}, "drum_map": "soundcraft"}]
}
```

## R&B/neo-soul

**BPM:** 65–100; example 82. **Swing:** 0.58. **Main:** relaxed backbeat, sparse kick and soft hat subdivisions. **Variation:** move a ghost snare into the space before the backbeat. **Fill:** restrained snare ghosts and tom at bar 4. Keep the pocket human and uncluttered.

```json
{
  "bpm": 82, "time_signature": [4, 4], "output": "rnb-drums.mid",
  "tracks": [{"name": "RNB Drums", "type": "drums", "steps": 16, "swing": 0.58, "bars": 4, "humanize": 0.04, "seed": 24,
    "pattern": {"kick": "x.....x...x.....", "snare": "....g.......x...", "hat": "x..x.x..x..x.x.."},
    "offset_ms": {"snare": 12}, "fill": {"every": 4, "pattern": {"snare": "......g.x...X..g", "tom_low": "............x..."}}, "drum_map": "soundcraft"}]
}
```

## hip-hop

**BPM:** 70–100; example 90. **Swing:** 0.56. **Main:** half-time snare on beat 3 with a syncopated kick. **Variation:** add a quiet kick pickup, retaining open space. **Fill:** a short ghost-note/snare turn. A slightly late snare supports a laid-back feel; adjust only to taste.

```json
{
  "bpm": 90, "time_signature": [4, 4], "output": "hip-hop-drums.mid",
  "tracks": [{"name": "Hip Hop Drums", "type": "drums", "steps": 16, "swing": 0.56, "bars": 4, "humanize": 0.04, "seed": 25,
    "pattern": {"kick": "x.....x...x.....", "snare": "........x.......", "hat": "x..x.x..x..x.x.."},
    "offset_ms": {"snare": 16}, "fill": {"every": 4, "pattern": {"snare": "........g...X..g"}}, "drum_map": "soundcraft"}]
}
```

## trap

**BPM:** 130–160; example 144 (often felt in half-time). **Swing:** 0.50. **Main:** half-time snare, sparse kick and rapid but controlled 16th hats. **Variation:** use a few 32nd steps only when a denser hat phrase is wanted. **Fill:** a short hat roll; the built-in map supports hats but not shaker.

```json
{
  "bpm": 144, "time_signature": [4, 4], "output": "trap-drums.mid",
  "tracks": [{"name": "Trap Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 26,
    "pattern": {"kick": "x.....x...x.....", "snare": "........x.......", "hat": "x.x.x.x.x.x.x.x."},
    "fill": {"every": 4, "pattern": {"hat": "xxxxxxxxXXXXXXXX"}}, "drum_map": "soundcraft"}]
}
```

## lo-fi

**BPM:** 65–90; example 78. **Swing:** 0.58. **Main:** soft half-time backbeat, sparse kick and uneven-feeling hats. **Variation:** ghost snare pickup. **Fill:** understated ghost notes. A small positive snare offset gives a late pocket; it does not emulate tape or a live drummer.

```json
{
  "bpm": 78, "time_signature": [4, 4], "output": "lofi-drums.mid",
  "tracks": [{"name": "Lo Fi Drums", "type": "drums", "steps": 16, "swing": 0.58, "bars": 4, "humanize": 0.04, "seed": 27,
    "pattern": {"kick": "x.......x...x...", "snare": "........x...g...", "hat": "x..x.x..x..x.x.."},
    "offset_ms": {"snare": 18}, "fill": {"every": 4, "pattern": {"snare": "........g...x..g"}}, "drum_map": "soundcraft"}]
}
```

## house

**BPM:** 118–130; example 124. **Swing:** 0.50. **Main:** four-on-the-floor kick, backbeat and even closed hats. **Variation:** open hat on offbeats. **Fill:** a tight snare/clap lift. Keep the grid precise; use a confirmed GM-compatible plugin and `gm` map if a clap is desired because built-in clap differs from a GM side stick but is supported.

```json
{
  "bpm": 124, "time_signature": [4, 4], "output": "house-drums.mid",
  "tracks": [{"name": "House Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.01, "seed": 28,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x.", "open_hat": "..x...x...x...x."},
    "fill": {"every": 4, "pattern": {"snare": "....x...x.x.XxXx"}}, "drum_map": "soundcraft"}]
}
```

## techno

**BPM:** 125–145; example 134. **Swing:** 0.50. **Main:** unwavering four-on-the-floor kick, sparse snare/clap and steady hats. **Variation:** shift an open hat to a phrase accent. **Fill:** brief tom/snare build. Keep timing tight and humanize minimal.

```json
{
  "bpm": 134, "time_signature": [4, 4], "output": "techno-drums.mid",
  "tracks": [{"name": "Techno Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.01, "seed": 29,
    "pattern": {"kick": "x...x...x...x...", "snare": "........x.......", "hat": "x.x.x.x.x.x.x.x.", "open_hat": "..x...x...x...x."},
    "fill": {"every": 4, "pattern": {"tom_hi": "............x.x.", "snare": "........x...X..."}}, "drum_map": "soundcraft"}]
}
```

## rock/indie

**BPM:** 90–150; example 120. **Swing:** 0.50. **Main:** straight eighth-note hats, solid kick and backbeat. **Variation:** open hat or crash at a section boundary. **Fill:** short tom/snare pickup. This MIDI pattern does not encode a live drum performance or acoustic kit tone.

```json
{
  "bpm": 120, "time_signature": [4, 4], "output": "rock-indie-drums.mid",
  "tracks": [{"name": "Rock Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.03, "seed": 30,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x."},
    "fill": {"every": 4, "pattern": {"tom_low": "............x.x.", "snare": "........x.x.XxXx"}}, "drum_map": "soundcraft"}]
}
```

## funk

**BPM:** 90–120; example 104. **Swing:** 0.52. **Main:** syncopated kick, crisp backbeat and rests in the hats. **Variation:** add a quiet ghost snare between backbeats. **Fill:** compact snare/tom pickup. Let the spaces define the groove; a MIDI kit does not supply a funk performance feel by itself.

```json
{
  "bpm": 104, "time_signature": [4, 4], "output": "funk-drums.mid",
  "tracks": [{"name": "Funk Drums", "type": "drums", "steps": 16, "swing": 0.52, "bars": 4, "humanize": 0.03, "seed": 31,
    "pattern": {"kick": "x..x..x...x..x..", "snare": "....x..g....x...", "hat": "x.x.x.x.x.x.x.x."},
    "fill": {"every": 4, "pattern": {"snare": "....g...x.x.XxXx", "tom_hi": "............x..."}}, "drum_map": "soundcraft"}]
}
```

## jazz

**BPM:** 80–180; example 116. **Swing:** 0.60. **Main:** ride-led pulse with a light two/four backbeat. **Variation:** sparse kick punctuation and snare ghost notes. **Fill:** short ride/snare phrase. This step grid shifts offbeat 16ths; it is a simplified swing sketch, not a ride cymbal transcription.

```json
{
  "bpm": 116, "time_signature": [4, 4], "output": "jazz-drums.mid",
  "tracks": [{"name": "Jazz Drums", "type": "drums", "steps": 16, "swing": 0.6, "bars": 4, "humanize": 0.03, "seed": 32,
    "pattern": {"kick": "x...............", "snare": "....g.......x...", "ride": "x..x.x..x..x.x.."},
    "fill": {"every": 4, "pattern": {"ride": "x..x.x..x.x.XxXx", "snare": "....g.......x..."}}, "drum_map": "soundcraft"}]
}
```

## latin/reggaeton

**BPM:** 85–110; example 96. **Swing:** 0.50. **Main:** straight dembow-inspired kick/snare placements with restrained hats. **Variation:** add an offbeat hat accent. **Fill:** a short snare pickup. This is a broad pop-reggaeton sketch; it does not encode clave or represent all Latin rhythms. Seek a specific reference for a regional pattern.

```json
{
  "bpm": 96, "time_signature": [4, 4], "output": "latin-reggaeton-drums.mid",
  "tracks": [{"name": "Reggaeton Drums", "type": "drums", "steps": 16, "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 33,
    "pattern": {"kick": "x.....x...x.....", "snare": "....x.......x...", "hat": "x...x...x...x..."},
    "fill": {"every": 4, "pattern": {"snare": "....x...x.x.XxXx"}}, "drum_map": "soundcraft"}]
}
```

## afrobeats

**BPM:** 95–115; example 104. **Swing:** 0.53. **Main:** light interlocking kick, backbeat and hats with open space. **Variation:** shift a kick pickup while keeping the vocal pocket clear. **Fill:** brief tom/snare response. This contemporary Afrobeats sketch is not an Afrobeat arrangement or a definition of African music; adapt it to a named artist or recording.

```json
{
  "bpm": 104, "time_signature": [4, 4], "output": "afrobeats-drums.mid",
  "tracks": [{"name": "Afrobeats Drums", "type": "drums", "steps": 16, "swing": 0.53, "bars": 4, "humanize": 0.03, "seed": 34,
    "pattern": {"kick": "x...x..x....x...", "snare": "....x.......x...", "hat": "x..x.x..x..x.x.."},
    "fill": {"every": 4, "pattern": {"tom_hi": "............x...", "snare": "........x.x.XxXx"}}, "drum_map": "soundcraft"}]
}
```

GM-only sounds such as shaker, tambourine and cowbell require a confirmed GM-compatible plugin and `drum_map: "gm"`. The built-in `drum_synth` does not produce these sounds. Custom maps require user-supplied or user-confirmed voice-to-note assignments.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); genre rhythm prompts adapted into independently written, source-checked SoundCraft MIDI examples. -->
