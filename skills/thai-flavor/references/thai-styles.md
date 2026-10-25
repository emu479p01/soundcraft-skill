# Thai style starting points

These are compositional choices for a fixed-pitch, equal-tempered MIDI workflow. Every example is four bars of quantized 4/4, with one chord per bar and a four-bar drum pattern. The Western triads, chord sequences, quantization and built-in drum proxies are fusion approximations; they are not claims about authentic traditional harmony or performance. BPM figures are starting points, not definitions. All examples use `drum_map: "soundcraft"`, the built-in custom map. `C=0` means pitch class 0 is C, 1 C-sharp/D-flat, through 11 B. For modal rows, PC arrays are listed center-first and then by the reference modal ordering, not ascending C order; this makes the chosen center explicit. PCs are not an instruction to harmonize every note with Western chords.

The pinned khaen reference sets below follow Parijat Namsanga's ethnomusicology thesis (2010), printed pp. 18–19, PDF pp. 32–33 (zero-based PDF pages 31–32): [primary thesis PDF](https://thesis.swu.ac.th/swuthesis/Ethno/Pariyat_N.pdf). A 2023 Bunditpatanasilpa Institute research report corroborates the long-way/short-way distinction and pitch sets, printed pp. 110–115, PDF pp. 120–125: [primary report PDF](https://media.bpi.ac.th/admin/attach/w2/f20241018133825_1E7vntBR9X.pdf). Prakrit Yaowapan's 2014 comparative paper also corroborates Lai yai and noi sets and discusses faster long-way playing and affect: [primary paper](https://doi.org/10.5539/ass.v10n4p255). The sets are transcribed references, not fixed tuning across khaen or performers.

Ching (ฉิ่ง) has multiple normal and special patterns; Suwannee Choosen's Chulalongkorn thesis abstract reports analysis of 690 pieces: [primary thesis record](https://www.car.chula.ac.th/display7.php?bib=b1739753). This supports avoiding one universal ching sequence. Cymbal proxies below do not encode a ching pattern.

## Luk thung (ลูกทุ่ง)

- **Mode and PC set:** Creative C-centered major pentatonic, `[0, 2, 4, 7, 9]` (C, D, E, G, A). This is one optional melodic palette, not a defining or universal Luk thung mode. Typical melodic ornaments and harmony depend on song and era; no single progression is asserted here.
- **Progression:** Illustrative C–Am–F–G; Western pop triads chosen for a contemporary song-led sketch, not a traditional formula. C major chords include F's A and C, but the F chord's F is outside the stated pentatonic melody palette; the melody palette does not limit accompaniment.
- **Tempo/groove:** 96 BPM starting point; steady, gently lilting 4/4. Ching (ฉิ่ง)→`ride` for sustained bright timekeeping proxy; chap (ฉาบ)→`crash` at phrase boundary for a broad cymbal accent; klong yao (กลองยาว)→`tom_mid` for pitched body. These proxy sounds do not reproduce the named instruments.
- **Chords spec:**

```json
{
  "bpm": 96, "time_signature": [4, 4], "output": "luk-thung-chords.mid",
  "tracks": [{"name": "Luk Thung Chords", "type": "chords",
    "progression": ["C", "Am", "F", "G"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 78, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 96, "time_signature": [4, 4], "output": "luk-thung-drums.mid",
  "tracks": [{"name": "Luk Thung Groove", "type": "drums", "steps": 16,
    "swing": 0.53, "bars": 4, "humanize": 0.02, "seed": 41,
    "pattern": {"kick": "x...x..x....x...", "snare": "....x.......x...",
      "ride": "x.x.x.x.x.x.x.x.", "tom_mid": "............x..."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx",
      "tom_mid": "............x.x."}}, "drum_map": "soundcraft"}]
}
```

## Mor lam (หมอลำ): Lai yai (ลายใหญ่)

- **Mode and PC set:** Pinned reference, center A, `[9, 0, 2, 4, 7]` (A, C, D, E, G), drone E–A. This is the reference's modal center/order, not a universal tuning. Yai and noi share a minor-pentatonic interval pattern under transposition, but not the same absolute pitch classes: yai includes E, while noi includes F. They also have different centers, drone references, contours and melodic emphasis. Yai and sut sanaen share the absolute A–C–D–E–G collection, with different centers and drone references.
- **Progression:** Illustrative modal-symbol sketch `Am–G–Am–G`; Western minor/major triads are a fusion accompaniment choice, not an ethnographic transcription. Omit a `key` field; A minor would misrepresent the mode.
- **Tempo/groove:** 84 BPM starting point for a spacious long-way phrase; slower or free-tempo Mor lam exists. Ching→`ride` for bright sustained pulse, chap→`crash` for phrase accents, thon (โทน)→`tom_low` for a low pitched-body proxy. None is an authentic timbre or full rhythm.
- **Chords spec:**

```json
{
  "bpm": 84, "time_signature": [4, 4], "output": "mor-lam-yai-chords.mid",
  "tracks": [{"name": "Lai Yai Chords", "type": "chords",
    "progression": ["Am", "G", "Am", "G"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 70, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 84, "time_signature": [4, 4], "output": "mor-lam-yai-drums.mid",
  "tracks": [{"name": "Lai Yai Groove", "type": "drums", "steps": 16,
    "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 42,
    "pattern": {"kick": "x.......x.......", "snare": "........x.......",
      "ride": "x...x...x...x...", "tom_low": "............x..."},
    "fill": {"every": 4, "pattern": {"tom_low": "............x.x.",
      "snare": ".............g.x"}}, "drum_map": "soundcraft"}]
}
```

## Mor lam (หมอลำ): Lai noi (ลายน้อย)

- **Mode and PC set:** Pinned reference, center D, `[2, 5, 7, 9, 0]` (D, F, G, A, C), drone D–A. Yai shares the minor-pentatonic interval pattern under transposition, but its absolute collection includes E where noi includes F; its center A, E–A drone reference and melodic contour also differ. Do not treat the two modes as interchangeable.
- **Progression:** Illustrative modal-symbol sketch `Dm–C–Dm–C`; Western minor/major triads are a fusion choice, not an authentic traditional progression. Omit `key`; D minor does not represent the mode. A slower/free phrase may be more appropriate to a particular reference.
- **Tempo/groove:** 80 BPM starting point, spacious long-way feel. Ching→`open_hat` for a sustained/open brightness contrast; chap→`crash` as a phrase marker; rammana (รำมะนา)→`tom_mid` for a pitched body proxy. These mappings do not recreate their sounds or playing techniques.
- **Chords spec:**

```json
{
  "bpm": 80, "time_signature": [4, 4], "output": "mor-lam-noi-chords.mid",
  "tracks": [{"name": "Lai Noi Chords", "type": "chords",
    "progression": ["Dm", "C", "Dm", "C"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 68, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 80, "time_signature": [4, 4], "output": "mor-lam-noi-drums.mid",
  "tracks": [{"name": "Lai Noi Groove", "type": "drums", "steps": 16,
    "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 43,
    "pattern": {"kick": "x.......x.......", "tom_mid": "............x...",
      "open_hat": "x.......x......."},
    "fill": {"every": 4, "pattern": {"tom_mid": "...........x.x..",
      "tom_low": "..............x."}}, "drum_map": "soundcraft"}]
}
```

## Mor lam (หมอลำ): Lai sut sanaen (ลายสุดสะแนน)

- **Mode and PC set:** Pinned short-way reference, center G, `[7, 9, 0, 2, 4]` (G, A, C, D, E), with G drone reference. The set is not fixed tuning or all performers' practice.
- **Progression:** Illustrative modal-symbol sketch `G–C–G–D`; Western major triads approximate a contemporary drone-centered accompaniment. Omit `key`; G major does not stand for this mode.
- **Tempo/groove:** 112 BPM starting point for a brighter short-way sketch. The label does not force speed. Ching→`ride` for bright pulse, chap→`open_hat` at an accent for open/closed contrast, klong yao→`tom_hi` for a higher pitched-body proxy. These are limited timbral stand-ins.
- **Chords spec:**

```json
{
  "bpm": 112, "time_signature": [4, 4], "output": "mor-lam-sut-chords.mid",
  "tracks": [{"name": "Lai Sut Sanaen Chords", "type": "chords",
    "progression": ["G", "C", "G", "D"], "chord_length": "1bar",
    "voicing": "open", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 74, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 112, "time_signature": [4, 4], "output": "mor-lam-sut-drums.mid",
  "tracks": [{"name": "Lai Sut Sanaen Groove", "type": "drums", "steps": 16,
    "swing": 0.52, "bars": 4, "humanize": 0.02, "seed": 44,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...",
      "ride": "x.x.x.x.x.x.x.x.", "tom_hi": "............x..."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx",
      "tom_hi": "............x.x."}}, "drum_map": "soundcraft"}]
}
```

## Thai pop (ป๊อปไทย)

- **Mode and PC set:** Optional C-centered major pentatonic `[0, 2, 4, 7, 9]`; a creative melodic palette only. Thai pop can use other scales and chromatic notes; no single mode is implied.
- **Progression:** Illustrative C–G–Am–F contemporary pop sequence, not specific to Thai pop and not necessarily constrained to pentatonic harmony.
- **Tempo/groove:** 104 BPM starting point, straight 4/4. Ching→`ride` for bright subdivision proxy, chap→`crash` for section accent, thon→`tom_low` for pitched low-body proxy. Do not describe these as acoustic Thai percussion.
- **Chords spec:**

```json
{
  "bpm": 104, "time_signature": [4, 4], "key": "C major", "output": "thai-pop-chords.mid",
  "tracks": [{"name": "Thai Pop Chords", "type": "chords",
    "progression": ["C", "G", "Am", "F"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 78, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 104, "time_signature": [4, 4], "output": "thai-pop-drums.mid",
  "tracks": [{"name": "Thai Pop Groove", "type": "drums", "steps": 16,
    "swing": 0.5, "bars": 4, "humanize": 0.02, "seed": 45,
    "pattern": {"kick": "x...x..x....x...", "snare": "....x.......x...",
      "ride": "x.x.x.x.x.x.x.x.", "tom_low": "............x..."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx",
      "tom_mid": "............x.x."}}, "drum_map": "soundcraft"}]
}
```

## Sam cha (สามช่า)

- **Mode and PC set:** Optional C-centered major pentatonic `[0, 2, 4, 7, 9]` for a bright melodic idea. This is a creative choice; Sam cha does not prescribe this scale.
- **Progression:** Illustrative C–F–G–C triads for a straightforward dance-pop sketch, not an asserted standard Sam cha progression.
- **Tempo/groove:** 120 BPM starting point in 4/4 with a buoyant straight pulse. Sam cha is a dance-groove label; it is not sam chan and its name alone does not imply 3/4. Ching→`ride` for bright timekeeping, chap→`crash` for broad phrase punctuation, klong yao→`tom_mid` for pitched-body proxy. None is a claim of authentic timbre or traditional pattern.
- **Chords spec:**

```json
{
  "bpm": 120, "time_signature": [4, 4], "key": "C major", "output": "sam-cha-chords.mid",
  "tracks": [{"name": "Sam Cha Chords", "type": "chords",
    "progression": ["C", "F", "G", "C"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "stabs", "velocity": 84, "voice_leading": true}]
}
```

- **Drums spec:**

```json
{
  "bpm": 120, "time_signature": [4, 4], "output": "sam-cha-drums.mid",
  "tracks": [{"name": "Sam Cha Groove", "type": "drums", "steps": 16,
    "swing": 0.52, "bars": 4, "humanize": 0.02, "seed": 46,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...",
      "ride": "x.x.x.x.x.x.x.x.", "open_hat": "..x...x...x...x."},
    "fill": {"every": 4, "pattern": {"snare": "....x...x.x.XxXx",
      "tom_mid": "............x.x."}}, "drum_map": "soundcraft"}]
}
```

## Fusion guidance

Keep one clearly identified reference element, such as a modal center/drone or a spacious vocal phrase, and add a restrained pop/EDM layer around it. Preserve room for melodic contour and ornaments; avoid making the chord loop dictate a mode's identity. If using the pinned lai references, keep the selected center and drone legible. Quantized 4/4 and equal-tempered chords are explicit production choices. For percussion, use only mapped supported voices and describe their proxy role; a real performer or recording reference is needed for idiomatic ching or drum patterns. Do not label a produced fusion sketch as a traditional transcription.
