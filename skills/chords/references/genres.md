# Chord genre starting points

Working BPM ranges and patterns below are adaptable composition choices, not rigid genre definitions or transcriptions. Follow the user's artist, song and regional references. Each JSON example is a four-bar, 4/4 MIDI sketch with one chord per bar; it supplies notes, not an audio patch or complete arrangement. Save it in the user's workspace with a fresh output filename, then run commands from the chords skill directory: `python ../soundcraft-core/scripts/make_midi.py "/absolute/work/genre.json" --json`. Never save artifacts into an installed plugin cache.

Read the owned-plugin corpus first as described in SKILL.md. All examples use rooted harmony and can be auditioned with built-in `subtractive_synth`; assign the instrument after import, not through an unsupported spec field. Keys/guitar/bell/mallet descriptions indicate synth approximations, not acoustic or culturally specific instrument authenticity. Optional free suggestions use [Surge XT](https://surge-synthesizer.github.io/), an open-source synth; [vendor downloads](https://surge-synthesizer.github.io/downloads/) were checked 2026-10-25. These are patch directions, not guaranteed named factory presets. Verify the installed build and runtime ID; never download or install automatically. No format/OS claim is made here.

Roman numerals follow the parser's key-relative convention: major keys use major-scale degrees; minor keys use natural minor degrees, so VI and VII are already flattened relative to parallel major. Case controls chord quality; V7 in minor supplies the dominant's raised third. In major reference keys, bIII/bVI/bVII and iv describe modal interchange. Each table row names its key; symbols and numerals denote matching roots and chord tones. Extensions must fit the melody. Use rootless only for suitable seventh/extended harmonies with a separate bass supplying roots; none of these examples assumes one. For reharmonization, announce exactly one strategy before acting; these alternatives do not authorize combining strategies.

`stabs` attacks beats 1 and 3, `block` each quarter note, and arpeggios each sixteenth. `custom` uses 16 steps (`x` normal, `X` accent, `g` ghost, `.` no new attack); notes sustain until the next attack/chord boundary. Short synth envelopes produce detached comping; dots alone do not cut off notes. Chord tracks do not accept drum-only swing/offset fields. Voice leading is enabled in all examples.

## pop

**BPM/feel:** 90–130 BPM; example 112. Straight eighth-note pulse and clear phrases.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | C G Am F | I V vi IV |
| G major | G Em C D | I vi IV V |
| C major | F C Dm G | IV I ii V |

**Voicing/rhythm:** Close or open triads with common tones; pad for sustained support or block for a steady pulse. Add a ninth selectively under a compatible melody.

**Instruments:** Built-in `subtractive_synth` with a soft sustained tone; free [Surge XT](https://surge-synthesizer.github.io/downloads/) with a rounded polyphonic pad.

```json
{
  "bpm": 112, "time_signature": [4, 4], "key": "C major", "output": "pop.mid",
  "tracks": [{"name": "Pop Chords", "type": "chords",
    "progression": ["C", "G", "Am", "F"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 84, "voice_leading": true}]
}
```

## Thai pop/Luk thung

**BPM/feel:** 75–125 BPM; example 96. Song-led phrasing; choose a straight or gently lilting accompaniment to match the reference.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | C Am F G | I vi IV V |
| A minor | Am Dm E7 Am | i iv V7 i |
| G major | G C D G | I IV V I |

**Voicing/rhythm:** Open rooted triads and restrained strums leave room for vocal ornaments. This combined index entry covers distinct practices: choose Thai pop or Luk thung from the brief rather than treating them as interchangeable. These are contemporary accompaniment sketches, not traditional-authenticity claims. Use a musical reference for finer stylistic detail.

**Instruments:** Built-in `subtractive_synth` as a plucked or sustained approximation; free [Surge XT](https://surge-synthesizer.github.io/downloads/) with a light plucked-string-style tone, not a claim to reproduce a traditional instrument.

```json
{
  "bpm": 96, "time_signature": [4, 4], "key": "C major", "output": "thai-pop-luk-thung.mid",
  "tracks": [{"name": "Thai Pop Chords", "type": "chords",
    "progression": ["C", "Am", "F", "G"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "strum_ms": 12, "velocity": 78, "voice_leading": true}]
}
```

## ballad

**BPM/feel:** 60–90 BPM; example 72. Unhurried sustained harmony with breathing space.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | C Am Dm G | I vi ii V |
| G major | G Em C D | I vi IV V |
| C major | C F Fm C | I IV iv I |

**Voicing/rhythm:** Open voicings and pad or restrained arp-up; keep the top voice singable. Borrowed iv in option three darkens the return to tonic.

**Instruments:** Built-in `subtractive_synth` as a soft pad; free [Surge XT](https://surge-synthesizer.github.io/downloads/) with mellow keys-style or pad tones.

```json
{
  "bpm": 72, "time_signature": [4, 4], "key": "C major", "output": "ballad.mid",
  "tracks": [{"name": "Ballad Chords", "type": "chords",
    "progression": ["C", "F", "Fm", "C"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "strum_ms": 12, "velocity": 72, "voice_leading": true}]
}
```

## R&B/neo-soul

**BPM/feel:** 65–110 BPM; example 82. Relaxed pocket, sustained color tones and vocal space.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | Dm9 G13 Cmaj9 Am9 | ii9 V13 Imaj9 vi9 |
| C major | Fmaj9 Em7 Dm9 G9 | IVmaj9 iii7 ii9 V9 |
| D minor | Dm9 Gm9 A7b9 Dm9 | i9 iv9 V7b9 i9 |

**Voicing/rhythm:** Drop2 or open voicings, smoothing thirds and sevenths across changes. Rootless is an option only on suitable extended chords with a separate root-playing bass; this example stays rooted. Start with pad; manually placed comping uses custom steps.

**Instruments:** Built-in `subtractive_synth` with a rounded keys-like envelope; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for a mellow electric-keys-style approximation.

```json
{
  "bpm": 82, "time_signature": [4, 4], "key": "C major", "output": "rnb-neo-soul.mid",
  "tracks": [{"name": "RNB Chords", "type": "chords",
    "progression": ["Dm9", "G13", "Cmaj9", "Am9"], "chord_length": "1bar",
    "voicing": "drop2", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 76, "voice_leading": true}]
}
```

## hip-hop

**BPM/feel:** 75–105 BPM; example 90. Spacious repeating loop with attacks around the drum pocket.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| A minor | Am7 Fmaj7 Dm7 E7 | i7 VImaj7 iv7 V7 |
| C major | Cmaj7 Am7 Dm7 G7 | Imaj7 vi7 ii7 V7 |
| D minor | Dm7 Bbmaj7 Gm7 A7 | i7 VImaj7 iv7 V7 |

**Voicing/rhythm:** Open midrange voicings and sparse pad attacks; arp-down can add motion without more chord changes. Preserve room for bass/voice. Humanize adds seeded variation, not a guaranteed late pocket.

**Instruments:** Built-in `subtractive_synth` with a dark sustained tone; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for muted keys-style sounds.

```json
{
  "bpm": 90, "time_signature": [4, 4], "key": "A minor", "output": "hip-hop.mid",
  "tracks": [{"name": "Hip Hop Chords", "type": "chords",
    "progression": ["Am7", "Fmaj7", "Dm7", "E7"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 76, "humanize": 0.04, "seed": 12, "voice_leading": true}]
}
```

## trap

**BPM/feel:** 130–160 BPM; example 144. Half-time perception around 65–80 BPM; sparse harmonic movement.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| A minor | Am F G Em | i VI VII v |
| E minor | Em C Am B7 | i VI iv V7 |
| D minor | Dm Bb C Am | i VI VII v |

**Voicing/rhythm:** Close upper voicings with restrained arp-up or pad. Let a separate bass carry low-end weight; avoid doubling low chord roots over it. Fast hats belong in drums rather than extra chord changes.

**Instruments:** Built-in `subtractive_synth` as a soft pluck; free [Surge XT](https://surge-synthesizer.github.io/downloads/) with a bell-like synth tone.

```json
{
  "bpm": 144, "time_signature": [4, 4], "key": "A minor", "output": "trap.mid",
  "tracks": [{"name": "Trap Chords", "type": "chords",
    "progression": ["Am", "F", "G", "Em"], "chord_length": "1bar",
    "voicing": "close", "range": [60, 84], "octave": 4,
    "rhythm": "arp-up", "velocity": 74, "voice_leading": true}]
}
```

## lo-fi

**BPM/feel:** 65–95 BPM; example 78. Gentle loop with modest timing and velocity variation.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | Cmaj7 Am7 Dm9 G9 | Imaj7 vi7 ii9 V9 |
| D minor | Dm9 Gm7 Bbmaj7 A7b9 | i9 iv7 VImaj7 V7b9 |
| C major | Fmaj7 Fm7 Em7 Am7 | IVmaj7 iv7 iii7 vi7 |

**Voicing/rhythm:** Open sevenths/ninths with sustained pad rhythm. Borrowed iv7 in option three adds chromatic inner motion. Keep humanize subtle; chord tracks have no swing field.

**Instruments:** Built-in `subtractive_synth` for a soft pad; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for muted keys-style sounds. Tape/noise processing is separate from the MIDI.

```json
{
  "bpm": 78, "time_signature": [4, 4], "key": "C major", "output": "lo-fi.mid",
  "tracks": [{"name": "Lo Fi Chords", "type": "chords",
    "progression": ["Cmaj7", "Am7", "Dm9", "G9"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 72, "humanize": 0.04, "seed": 12, "voice_leading": true}]
}
```

## house

**BPM/feel:** 118–130 BPM; example 124. Steady dance pulse with offbeat comping.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| A minor | Am7 Dm7 G7 Cmaj7 | i7 iv7 VII7 IIImaj7 |
| C major | Cmaj7 Fmaj7 Dm7 G7 | Imaj7 IVmaj7 ii7 V7 |
| A minor | Am F C G | i VI III VII |

**Voicing/rhythm:** Close or drop2 voicings with short decay/release. Use custom `..x...x...x...x.` for eighth-note offbeats; stabs would hit beats 1 and 3. Custom notes sustain until the next hit, so envelope shape supplies detachment.

**Instruments:** Built-in `subtractive_synth` for a percussive chord tone; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for organ-like or plucked synth comping.

```json
{
  "bpm": 124, "time_signature": [4, 4], "key": "A minor", "output": "house.mid",
  "tracks": [{"name": "House Chords", "type": "chords",
    "progression": ["Am7", "Dm7", "G7", "Cmaj7"], "chord_length": "1bar",
    "voicing": "drop2", "range": [48, 79], "octave": 4,
    "rhythm": "custom", "steps": "..x...x...x...x.", "velocity": 88, "voice_leading": true}]
}
```

## techno

**BPM/feel:** 125–145 BPM; example 134. Repetitive precise pulse; timbre and spacing carry development.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| A minor | Am Am F G | i i VI VII |
| C major | C Ab Bb C | I bVI bVII I |
| E minor | Em C Em D | i VI i VII |

**Voicing/rhythm:** Compact repeated cells, close voicings and minimal humanize. Option two borrows bVI and bVII from parallel minor while retaining a major tonic. Use precise custom pulses and supported timbral controls.

**Instruments:** Built-in `subtractive_synth` for a dry chord pulse; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for restrained metallic or filtered polyphonic tones.

```json
{
  "bpm": 134, "time_signature": [4, 4], "key": "A minor", "output": "techno.mid",
  "tracks": [{"name": "Techno Chords", "type": "chords",
    "progression": ["Am", "Am", "F", "G"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "custom", "steps": "x...x...x...x...", "velocity": 90, "voice_leading": true}]
}
```

## rock/indie

**BPM/feel:** 90–150 BPM; example 120. Straight pulse; contrast sustained sections and driving attacks.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| G major | G D Em C | I V vi IV |
| C major | C Bb F C | I bVII IV I |
| E minor | Em G D A | i III VII IV |

**Voicing/rhythm:** Rooted open voicings or power chords when requested; block with modest strum_ms. Borrowed bVII and major IV in minor are options, not obligations. Synth strums approximate timing, not a guitar performance.

**Instruments:** Built-in `subtractive_synth` as an open polyphonic synth; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for an indie synth layer or plucked approximation alongside guitars.

```json
{
  "bpm": 120, "time_signature": [4, 4], "key": "G major", "output": "rock-indie.mid",
  "tracks": [{"name": "Rock Chords", "type": "chords",
    "progression": ["G", "D", "Em", "C"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "block", "strum_ms": 12, "velocity": 92, "voice_leading": true}]
}
```

## funk

**BPM/feel:** 90–120 BPM; example 104. Tight syncopated comping with deliberate accents and spaces.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | C9 F9 C9 G9 | I9 IV9 I9 V9 |
| A minor | Am7 D9 Am7 E9 | i7 IV9 i7 V9 |
| C major | Dm9 G13 Dm9 G13 | ii9 V13 ii9 V13 |

**Voicing/rhythm:** Close or drop2 voicings and a percussive envelope; custom sixteenth attacks around the bass line. Dominant colors need not imply classical cadences. Rootless requires suitable extended chords and a separate root-playing bass.

**Instruments:** Built-in `subtractive_synth` as short keys-like comping; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for a clavinet-style synth approximation.

```json
{
  "bpm": 104, "time_signature": [4, 4], "key": "C major", "output": "funk.mid",
  "tracks": [{"name": "Funk Chords", "type": "chords",
    "progression": ["C9", "F9", "C9", "G9"], "chord_length": "1bar",
    "voicing": "drop2", "range": [48, 79], "octave": 4,
    "rhythm": "custom", "steps": "x..x..x...X..x..", "velocity": 86, "voice_leading": true}]
}
```

## jazz

**BPM/feel:** 80–180 BPM; example 116. Phrase-aware comping; example timing is straight, not encoded swing.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | Dm9 G13 Cmaj9 A7b9 | ii9 V13 Imaj9 VI7b9 |
| C major | Dm7 Db7 Cmaj7 Cmaj7 | ii7 bII7 Imaj7 Imaj7 |
| C major | Cmaj7 C#dim7 Dm7 G7 | Imaj7 #Idim7 ii7 V7 |

**Voicing/rhythm:** Drop2 extended voicings; rootless only with a separate bass supplying roots. Option two substitutes Db7 for G7 via their shared tritone; option three uses C#dim7 as a passing approach to Dm7. These are alternative reharmonization strategies, not an automatic bundle. Check melody tensions before altered dominants. Sparse stabs here are an audition pattern; use custom timing for actual comping.

**Instruments:** Built-in `subtractive_synth` as soft comping; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for mellow keys-style tones. Neither implies acoustic piano realism.

```json
{
  "bpm": 116, "time_signature": [4, 4], "key": "C major", "output": "jazz.mid",
  "tracks": [{"name": "Jazz Chords", "type": "chords",
    "progression": ["Dm9", "G13", "Cmaj9", "A7b9"], "chord_length": "1bar",
    "voicing": "drop2", "range": [48, 79], "octave": 4,
    "rhythm": "stabs", "velocity": 78, "voice_leading": true}]
}
```

## latin/reggaeton

**BPM/feel:** 85–110 BPM; example 96. Choose a specific style/reference; this example is a straight pop-reggaeton harmony sketch.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| A minor | Am F C G | i VI III VII |
| D minor | Dm Gm A7 Dm | i iv V7 i |
| C major | C Am Dm G7 | I vi ii V7 |

**Voicing/rhythm:** Close or open rooted voicings and sparse offbeats. Latin is a broad umbrella; reggaeton is not a substitute for all its rhythms. This chord pattern does not encode a clave or dembow drum arrangement. Use a style-specific reference for those parts.

**Instruments:** Built-in `subtractive_synth` with a short plucked envelope; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for bright keys-style or plucked synth sounds.

```json
{
  "bpm": 96, "time_signature": [4, 4], "key": "A minor", "output": "latin-reggaeton.mid",
  "tracks": [{"name": "Latin Pop Chords", "type": "chords",
    "progression": ["Am", "F", "C", "G"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "custom", "steps": "..x...x...x...x.", "velocity": 82, "voice_leading": true}]
}
```

## afrobeats

**BPM/feel:** 95–115 BPM; example 104. Light interlocking accompaniment, leaving space for percussion and vocals.

| Key | Symbols (one per bar) | Roman numerals |
|---|---|---|
| C major | C G Am F | I V vi IV |
| G major | G C Em D | I IV vi V |
| A minor | Am G F G | i VII VI VII |

**Voicing/rhythm:** Open triads, restrained added tones and sparse custom attacks; complement the bass. This is a contemporary Afrobeats sketch, not an Afrobeat arrangement or a definition of African music. Adapt to the artist/reference rather than a universal pattern.

**Instruments:** Built-in `subtractive_synth` as a light pluck; free [Surge XT](https://surge-synthesizer.github.io/downloads/) for rounded plucked or mallet-like synth tones.

```json
{
  "bpm": 104, "time_signature": [4, 4], "key": "C major", "output": "afrobeats.mid",
  "tracks": [{"name": "Afrobeats Chords", "type": "chords",
    "progression": ["C", "G", "Am", "F"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "custom", "steps": "x.....x...x..x..", "velocity": 78, "voice_leading": true}]
}
```

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); genre-oriented brief mapping and harmony options, independently written examples for SoundCraft. -->
