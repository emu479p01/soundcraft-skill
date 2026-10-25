# SoundCraft Skills — Design Spec

- วันที่: 2026-10-25
- สถานะ: รอรีวิว (Phase 1 ละเอียด, Phase 2–3 ระดับ roadmap)
- โปรแกรมเป้าหมาย: [storytold/soundcraft](https://github.com/storytold/soundcraft) (Rust DAW, pre-alpha)

## 1. เป้าหมาย

ชุด Agent Skills ที่ช่วย music producer ประหยัดเวลาในการทำเพลงด้วย SoundCraft:
สร้างชุดคอร์ด, สร้างแพทเทิร์นกลอง, หา/ติดตั้ง/ใช้ plugin (CLAP/VST3/AU) ที่ producer มี

**ผู้ใช้:** ใช้เองก่อน แล้วเผยแพร่ภายหลัง — จึงต้องออกแบบให้ทำงานข้าม OS (Windows/macOS/Linux)
และข้าม agent harness ได้ตั้งแต่แรก

**Harness ที่รองรับ:** Claude Code, OpenAI Codex (GPT), Google Antigravity

**เกณฑ์ความสำเร็จ v1**
1. User พิมพ์ชื่อคอร์ดเอง (`Am7 - Fmaj7 - C - G/B`) หรืออธิบายเป็นภาษาคน
   ("คอร์ดเศร้าแบบ lo-fi key D minor") แล้วได้ track คอร์ดใน SoundCraft ที่เล่นได้
2. User ขอกลองตามแนว/BPM แล้วได้ track กลองใน SoundCraft
3. User ถามว่ามี plugin อะไร / ควรใช้อะไร แล้วได้คำตอบจากการสแกนเครื่องจริง และโหลด plugin เข้า track ได้
4. ถ้า SoundCraft/MCP ใช้ไม่ได้ ยังได้ไฟล์ `.mid` ไปใช้ใน DAW อื่น
5. ติดตั้งได้ทั้ง 3 harness จาก repo เดียว
6. User ขอเสียง ("pad อุ่น ๆ", "808 ยาว") แล้วได้ `subtractive_synth` ที่ตั้งค่าแล้ว + บันทึกเป็น preset
7. User ส่งไฟล์ MIDI / track ที่มีอยู่ แล้วได้ key, ชื่อคอร์ด, เลขโรมัน และคำอธิบาย
8. ขอ "ลูกทุ่ง" / "หมอลำ" / "ป๊อปไทย" ใน chords/drums แล้วได้สำเนียงไทยที่ถูกต้อง

**ทั้งหมดแบ่งทำเป็น 3 phase** (ดู §10 Roadmap) — spec นี้ลงรายละเอียด **Phase 1**;
Phase 2–3 จะมี spec + plan ของตัวเองเมื่อ Phase ก่อนหน้าใช้งานได้จริง

**นอกขอบเขตทุก phase:** การดาวน์โหลด/รัน installer ของ plugin อัตโนมัติ

## 2. ข้อเท็จจริงของ SoundCraft ที่ออกแบบอิง

- มี MCP server ในตัว: `soundcraft-cli mcp` — tools `list_commands`, `execute`, `batch`,
  `inspect_session`, `new_session`, `open_session`, `save_session`, `import_audio`, `bounce_mix`, `parity`
- คำสั่งเป็น id + JSON params เช่น `mix.insert={"track":"Bass","plugin":"eq_7band"}`,
  `mix.instrument`, `track.new`, `file.import_midi`, `file.export_midi`
- Plugin ในตัว 25 ตัว (เช่น `subtractive_synth`, `drum_synth`, `eq_7band`, `compressor`)
- Plugin ภายนอก: CLAP, VST3, AU (macOS) — ไม่รองรับ VST2/AAX/LV2/LADSPA; สแกนจากโฟลเดอร์ระบบมาตรฐาน; ไม่มี registry/installer
- ไม่มีคำสั่งสร้างโน้ตที่มีเอกสาร → v1 สร้าง `.mid` แล้ว `file.import_midi`

**ต้องยืนยันจาก source ตอน implement** (บันทึกผลลง `soundcraft-commands.md`):
params ของ `file.import_midi`, `mix.instrument`, คำสั่งโหลด plugin ภายนอก, note map ของ `drum_synth`,
และความจำเป็นของ flag `--demo`

## 3. สถาปัตยกรรม

```
soundcraft-skill/
├── skills/
│   ├── soundcraft-core/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── make_midi.py          # CLI: JSON spec -> .mid + สรุปข้อความ
│   │   │   ├── scan_plugins.py       # CLI: สแกนโฟลเดอร์ plugin -> JSON + corpus
│   │   │   ├── analyze_midi.py       # CLI: .mid -> key, คอร์ด, เลขโรมัน (JSON/ข้อความ)
│   │   │   └── scmidi/
│   │   │       ├── midi_reader.py    # อ่าน SMF (ใช้ทั้ง analyze และ tests)
│   │   │       ├── analysis.py       # เดา key (pitch-class profile), จับคอร์ดต่อช่วงเวลา
│   │   │       ├── theory.py         # parse คอร์ด/เลขโรมัน, voicing, voice leading
│   │   │       ├── rhythm.py         # step string parser, swing, humanize, fill
│   │   │       ├── drums.py          # drum maps (gm, soundcraft, custom)
│   │   │       ├── spec.py           # validate JSON spec -> error ที่อ่านเข้าใจ
│   │   │       └── midi_writer.py    # เขียน SMF type 1 (stdlib ล้วน)
│   │   └── references/soundcraft-commands.md
│   ├── soundcraft-setup/SKILL.md
│   ├── chords/{SKILL.md, references/genres.md}
│   ├── drums/{SKILL.md, references/grooves.md}
│   ├── plugins/{SKILL.md, references/free-plugins.md}
│   ├── sound-design/{SKILL.md, references/synth-recipes.md}
│   ├── theory-coach/SKILL.md
│   └── thai-flavor/{SKILL.md, references/thai-styles.md}
├── .claude-plugin/{plugin.json, marketplace.json}   # Claude Code
├── .mcp.json                                        # Claude Code + Codex
├── .codex-plugin/plugin.json                        # Codex
├── .agents/plugins/marketplace.json                 # Codex marketplace
├── plugin.json, mcp_config.json                     # Antigravity
├── LICENSE, CREDITS.md                               # MIT (Chaiyaporn Santangjai) + เครดิต
├── install.py                                       # fallback installer
├── tests/
└── README.md                                        # ไทย + อังกฤษ
```

**หลักการ**
- `skills/` ชุดเดียวใช้ร่วมทุก harness
- Script ทั้งหมดอยู่ใน `soundcraft-core` (เพราะ harness บางตัว copy เฉพาะโฟลเดอร์ skill)
  skill อื่นอ้าง `../soundcraft-core/scripts/...` แบบ relative ต่อโฟลเดอร์ skill ตัวเอง
- Python 3.9+ stdlib ล้วน ไม่มี dependency
- Frontmatter ใช้เฉพาะฟิลด์ตาม Agent Skills spec (`name`, `description`, `license`, `metadata`)
  — `model:` (Claude-only, เพื่อประหยัดค่าใช้จ่าย) จะเพิ่มเฉพาะเมื่อทดสอบแล้วว่า Codex/Antigravity ไม่ error
- `install.py`: copy/symlink `skills/*` ไป `~/.agents/skills` (Codex) และ `~/.gemini/config/skills` (Antigravity),
  merge MCP config ลง `~/.codex/config.toml` และ `~/.gemini/config/mcp_config.json` ด้วย absolute path;
  มี `--dry-run` และ backup ไฟล์ config ก่อนแก้
- Manifest ทุกตัวตรวจกับ docs ทางการตอน implement (รูปแบบ marketplace ของ Claude/Antigravity
  และ key `mcpServers` ของ Codex ยังไม่ได้ยืนยัน)

**Data flow (chords/drums)**
คำขอ user → skill ตีความ (ใช้ references) → เขียน JSON spec ลงไฟล์ → `make_midi.py spec.json`
→ `.mid` + สรุปโน้ต → MCP `file.import_midi` → `mix.instrument` → (optional) `bounce_mix` ตรวจว่ามีเสียง

## 4. JSON Spec

```json
{
  "bpm": 90, "time_signature": [4, 4], "key": "D minor",
  "output": "lofi-sketch.mid",
  "tracks": [
    {
      "name": "Chords", "type": "chords",
      "progression": ["Dm9", "Gm7", {"chord": "Bbmaj7", "beats": 2}, "A7b9"],
      "chord_length": "1bar",
      "voicing": "open", "octave": 4,
      "rhythm": "pad", "velocity": 80, "humanize": 0.15, "repeat": 2
    },
    {
      "name": "Drums", "type": "drums",
      "steps": 16, "swing": 0.58, "bars": 8,
      "pattern": {
        "kick":  "x.....x...x.....",
        "snare": "....X.......X..g",
        "hat":   "x.x.x.x.x.x.x.x."
      },
      "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx"}},
      "drum_map": "gm"
    }
  ]
}
```

**Chords track**
- `progression`: string หรือ `{"chord", "beats"|"bars"}`; รองรับ string เดียวคั่นด้วย `-` หรือ `|`
- คุณภาพคอร์ด: triad, `m`, `dim`, `aug`, `sus2`, `sus4`, `5`, `6`, `m6`, `7`, `maj7`, `m7`, `mMaj7`,
  `m7b5`, `dim7`, `9`, `maj9`, `m9`, `11`, `m11`, `13`, `maj13`, `add9`, `add11`,
  alterations (`b5 #5 b9 #9 #11 b13`), slash chord (`G/B`)
- เลขโรมันเมื่อมี `key`: `i - VI - III - VII`, `ii7 - V7 - Imaj7`, รองรับ `bVII`, `V/V`
- `voicing`: `close` | `open` | `drop2` | `spread` | `rootless` (3-5-7-9 ช่วง MIDI ~56–74 ใช้เมื่อมีเบสเล่น root);
  `range: [low, high]` บังคับช่วงโน้ตตามเครื่องดนตรี (ค่าเริ่ม `[48, 79]`); voice leading อัตโนมัติ (เลือก inversion ที่ระยะรวมน้อยสุด) ปิดได้ด้วย `"voice_leading": false`
- `rhythm`: `block` | `pad` | `stabs` | `arp-up` | `arp-down` | `arp-updown` | `custom` (+ `"steps"` string)
- `bass_note`: `true` เพิ่ม root ต่ำ 1 octave (ค่าเริ่ม `false`)
- `strum_ms`: หน่วงโน้ตแต่ละตัวในคอร์ดจากล่างขึ้นบน (ค่าเริ่ม 0; แนะนำ ~15 สำหรับเปียโน/กีตาร์)

**Drums track**
- step chars: `x` ปกติ (vel 100), `X` accent (vel 120), `g` ghost (vel 45), `.` rest
- ความยาว string = `steps` ต่อห้อง (ค่าเริ่ม 16); ยาวกว่า 1 ห้องได้ถ้าเป็นจำนวนเท่าของ `steps`
- เสียง: `kick snare clap rim hat open_hat pedal_hat ride crash tom_hi tom_mid tom_low shaker tambourine cowbell perc`
- `swing` 0.5–0.75 (เลื่อน step คี่), `humanize` 0–1 (สุ่ม timing ±/velocity ด้วย seed คงที่ — `"seed"` กำหนดได้)
- `offset_ms`: เลื่อนเสียงบางชิ้นทั้งแพทเทิร์น เช่น `{"snare": 25}` (snare ลากหลังจังหวะสำหรับ lo-fi/hip-hop)
- `velocity`: override ค่า `x/X/g` ต่อเสียงได้ เช่น `{"hat": {"x": 85, "g": 40}}`
- `fill.every` N ห้อง แทนที่ห้องสุดท้ายของทุก N ห้องเฉพาะเสียงที่ระบุ
- `drum_map`: `gm` | `soundcraft` | object `{"kick": 36, ...}`

**Output**
- SMF type 1, PPQ 480, tempo + time signature ใน track 0, หนึ่ง track ต่อ spec track
- กลองใช้ channel 10, คอร์ดใช้ channel 1+ ตามลำดับ
- stdout: สรุปข้อความรายห้อง (`Bar 1: Dm9 = D3 A3 C4 E4 F4`) + path ไฟล์
- `--json` ให้สรุปเป็น JSON
- Exit code: 0 สำเร็จ, 2 spec ไม่ถูกต้อง (ข้อความระบุ field + ค่า + สิ่งที่ยอมรับ)
- Validate ก่อนเขียนเสมอ: pitch 0–127, velocity 1–127, start ≥ 0, duration > 0 — ไม่มีการเขียน output ที่ยังไม่ผ่าน validate

## 4.5 Thinking Framework (วิธีคิดที่ทุก skill ใช้ร่วมกัน)

ดัดแปลงแนวคิดจาก repo อ้างอิง (ดู §8) ให้เข้ากับ SoundCraft — เขียนใหม่ด้วยภาษาของเราเองทั้งหมด

**A. โครง SKILL.md มาตรฐาน** — ทุก skill มีหัวข้อเดียวกัน:
`When to use` → `Workflow` → `Style table` → `Spec pattern` → `Checks` → `Limits` → `Related skills`

**B. Brief → Parameters** (ใช้ใน chords/drums) — แตกคำขอเป็น
key/scale, bpm, bars, genre/feel, mood, density (sparse↔busy), energy arc, instrument/plugin เป้าหมาย
- ค่าที่ขาดให้เติมจาก Style table ของแนวนั้น แล้ว **บอก user ว่าเลือกอะไรให้**
- ถามเฉพาะเมื่อจำเป็นจริง (เช่นไม่รู้แนว และไม่มีบริบทเลย) ไม่เกิน 1–2 คำถาม แบบยืนยัน:
  "จะใช้ D minor 90 BPM สไตล์ lo-fi นะครับ โอเคไหม?" แทนคำถามปลายเปิด

**C. Preflight → Read state → Act → Re-read** (ทุกครั้งที่แตะ SoundCraft)
1. Preflight: MCP ตอบไหม (`list_commands`) — ล้ม = หยุดแล้วส่งไป `soundcraft-setup` / fallback `.mid`
2. Read state: `inspect_session` เอาชื่อ/id track จริง — **ห้ามเดา id**
3. Plugin: ค้นชื่อที่ตรงเป๊ะก่อนโหลด (ชื่อผิดตัวพิมพ์ = ล้ม)
4. ห้ามเขียนทับ track/clip ที่มีอยู่ เว้นแต่ user สั่ง — ค่าเริ่มคือสร้าง track ใหม่
5. หลังแก้ทุกครั้ง: `inspect_session` ยืนยันผล

**D. Generate → Measure → Adjust (สูงสุด 3 รอบ)**
- Measure ระดับ spec: อ่านสรุปโน้ตจาก `make_midi.py` ตรวจกับเจตนา (คอร์ดถูก, ช่วงเสียงอยู่ใน range, kick ตรงจังหวะ)
- Measure ระดับเสียง (ถ้ามี MCP): `bounce_mix` → มีเสียง (peak > -inf), ไม่ clip (peak ≤ 0 dBFS)
- ครบ 3 รอบแล้วยังไม่ผ่าน → รายงานสิ่งที่ติดและถาม user
- ผลแบ่ง **FAIL** (หยุด) / **WARN** (แจ้งแต่ไปต่อ)

**E. Error recovery classes** (ใน `soundcraft-commands.md`)
| Class | ตัวอย่าง | การแก้ |
|---|---|---|
| แก้ request | spec ผิด, ชื่อคำสั่ง/plugin ผิด | แก้แล้วรันใหม่ / `list_commands` หาคำสั่งใกล้เคียง |
| แก้ session state | track ไม่มี, transport กำลังเล่น | อ่าน state ใหม่ / หยุด transport ก่อนแก้โครงสร้าง |
| แก้ environment | SoundCraft ไม่เปิด, MCP ไม่ต่อ, ไฟล์เขียนไม่ได้ | ส่งไป setup / fallback `.mid` |

**F. ความรู้ดนตรีที่ฝังใน references**
- *Harmony* (`chords`): ขยายคอร์ดตามแนว (m→m9, maj→maj9, dom→9/13 สำหรับ R&B/jazz/neo-soul),
  rootless voicing เมื่อมีเบส, modal interchange (♭III ♭VI ♭VII iv), tritone sub, passing diminished;
  โหมด **reharmonize** — "ทำให้แจ๊สขึ้น/เศร้าขึ้น" ต้อง **ประกาศกลยุทธ์ 1 อย่างก่อน** แล้วค่อยแก้
- *Rhythm* (`drums`): velocity 3 ระดับ (accent/ปกติ/ghost), swing เฉพาะ off-beat 16th,
  snare ลากหลัง (lo-fi/hip-hop) vs ตรงเป๊ะ (house/techno), fill ทุก 4 หรือ 8 ห้อง,
  humanize แบบเบาเป็นค่าเริ่ม ("humanize มากเกินทำให้แนวที่ต้องแน่นเละ")
- *Style table* ต่อแนว: BPM range, feel, progression/groove ตัวอย่าง, instrument แนะนำ (built-in + plugin ฟรี)

**G. User Corpus** (`plugins`)
- ผลสแกน plugin เก็บที่ `~/.soundcraft-skills/plugins.json` (ชื่อ, format, path, หมวด: synth/drum/eq/comp/reverb/…)
- `chords`/`drums` อ่าน corpus เพื่อแนะนำ **plugin ที่ user มีจริง** ก่อน built-in หรือของฟรีที่ยังไม่ได้ติดตั้ง
- อ่านช่วงค่า parameter จาก MCP ก่อนตั้งค่าเสมอ; ลำดับ FX มาตรฐาน: EQ → comp → saturation → modulation → delay → reverb

**H. การรายงานผล** — ภาษาคนสั้น ๆ: ทำอะไรไป, เลือกค่าอะไรให้และเพราะอะไร, ไฟล์อยู่ไหน, ขั้นต่อไปที่แนะนำ

## 5. Skills

| Skill | หน้าที่ |
|---|---|
| `soundcraft-core` | เอกสารวิธีเรียก script + คำสั่ง MCP; ใช้ตรงได้สำหรับ "export เป็น .mid" |
| `soundcraft-setup` | เช็ก/แนะนำติดตั้ง SoundCraft + Python, ตั้ง MCP ตาม harness, smoke test |
| `chords` | ตีความคำขอ → spec → import → ตั้ง instrument (ค่าเริ่ม `subtractive_synth` หรือ plugin ที่ user ระบุ) |
| `drums` | ตีความ genre/BPM/feel → spec → import → `drum_synth` หรือ plugin กลองของ user (เลือก `drum_map`) |
| `plugins` | สแกน → รายงาน → แนะนำ plugin ฟรี (เปิดหน้าดาวน์โหลด, ไม่รัน installer) → โหลดเข้า track |
| `sound-design` | คำบรรยายเสียง → recipe ของ `subtractive_synth` (osc, filter, envelope, LFO) → อ่านช่วง param จาก MCP → ตั้งค่า → บันทึก preset; ถ้า user มี synth ภายนอก (corpus) ให้คำแนะนำ patch แทน |
| `theory-coach` | `.mid` ของ user หรือ `file.export_midi` จาก track → `analyze_midi.py` → อธิบาย key/คอร์ด/เลขโรมัน/voice leading และ "ทำไมฟังเป็นแบบนี้"; เสนอ reharm โดยส่งต่อ `chords` |
| `thai-flavor` | สำเนียงไทย: ลูกทุ่ง, หมอลำ (ลายใหญ่/ลายน้อย/ลายสุดสะแนน), ป๊อปไทย, สามช่า; pentatonic ไทย, แพทเทิร์นกลองยาว/โทน/รำมะนา/ฉิ่ง-ฉาบ map ลงเสียงกลอง GM; วิธีผสมกับ pop/EDM; ส่ง spec ให้ `chords`/`drums` สร้าง |

**sound-design recipes** (`synth-recipes.md`): pad, pluck, lead, bass, 808/sub, keys, brass-ish, arp —
แต่ละอันระบุ waveform, filter type/cutoff/resonance, ADSR amp+filter, LFO, unison/detune เป็นค่าที่อธิบายด้วย
หน่วยจริง (Hz, ms) แล้ว map ลง param ของ `subtractive_synth` ตอน implement (ชื่อ/ช่วง param ยืนยันจาก source)

**theory-coach analysis**: key ด้วย Krumhansl–Schmuckler profile (บอกความมั่นใจ + ทางเลือกอันดับ 2),
คอร์ดต่อช่วง (ค่าเริ่ม 1 beat, รวมช่วงที่ซ้ำ) ด้วย template matching ของ `theory.py` แบบย้อนกลับ;
ช่วงที่ไม่ชัดให้ติดป้าย `?` แทนการเดา

**คลังความรู้** (`genres.md`, `grooves.md`): pop, ป๊อปไทย/ลูกทุ่ง, ballad, R&B/neo-soul, hip-hop, trap, lo-fi,
house, techno, rock/indie, funk, jazz, latin/reggaeton, afrobeats — แต่ละแนวมี progression/voicing/rhythm หรือ
groove + BPM ทั่วไป ในรูป spec ตัวอย่างที่นำไปดัดแปลงได้ แนวที่ไม่มีในคลังให้ agent ใช้ทฤษฎีดนตรีเอง

**soundcraft-setup flow**
1. `soundcraft-cli --version` → ไม่มี: บอกวิธีติดตั้งตาม OS + ลิงก์ Releases, ทำต่อเมื่อ user ยืนยัน
2. Python 3 → ไม่มี: แนะนำ `winget install Python.Python.3` / `brew install python` / package manager, รันเมื่อ user อนุญาต
3. MCP `list_commands` → ไม่ได้: แสดงวิธีตั้งค่าของ harness ที่ใช้อยู่ หรือแนะนำ `install.py`
4. Smoke test: C–G–Am–F 4 ห้อง → import → `bounce_mix` → รายงาน peak/LUFS (peak > -inf = ผ่าน)

**plugins: โฟลเดอร์ที่สแกน**
- Windows: `%CommonProgramFiles%\VST3`, `%CommonProgramFiles%\CLAP`, `%LOCALAPPDATA%\Programs\Common\VST3`, `%LOCALAPPDATA%\Programs\Common\CLAP`
- macOS: `/Library/Audio/Plug-Ins/{VST3,CLAP,Components}`, `~/Library/Audio/Plug-Ins/{VST3,CLAP,Components}`
- Linux: `~/.vst3`, `~/.clap`, `/usr/lib/vst3`, `/usr/local/lib/vst3`, `/usr/lib/clap`, `/usr/local/lib/clap`, `$CLAP_PATH`
- รายงาน format ที่ไม่รองรับ (VST2 `.dll`/`.vst`, AAX, LV2) แยกเป็น warning
- `--extra-dir` เพิ่มโฟลเดอร์ได้

## 6. Error handling

- ไม่มี MCP / SoundCraft ไม่ทำงาน → ทุก skill ยังสร้าง `.mid` และบอก path ให้ลากเข้า DAW เอง
- Spec ผิด → exit 2 + ข้อความชัดเจน → agent แก้แล้วรันใหม่ (สูงสุด 3 รอบ แล้วถาม user)
- คำสั่ง MCP ผิด/เปลี่ยนเวอร์ชัน → skill ใช้ `list_commands` ค้นคำสั่งที่ใกล้เคียงก่อนแจ้ง user
- Plugin ไม่ขึ้น → แนะนำ restart/rescan + ข้อจำกัดที่รู้ (signed macOS ไม่โหลด VST3 ภายนอก, in-process crash)
- การกระทำที่แก้ระบบ (ติดตั้งโปรแกรม, แก้ config ของ harness) → ต้องให้ user ยืนยันก่อนเสมอ

## 7. Testing

- `python -m unittest` (stdlib):
  - theory: parse ทุกคุณภาพคอร์ด, slash, เลขโรมัน, voicing, voice leading
  - rhythm/drums: step parser, swing, humanize แบบ seed คงที่, fill, drum maps
  - spec: error message ของ input ผิด
  - midi_writer: อ่าน `.mid` ที่เขียนกลับด้วย reader ในเทสต์ ตรวจโน้ต/tick/tempo
  - scan_plugins: โฟลเดอร์จำลองใน temp dir
  - install.py: `--dry-run` กับ home จำลอง
- Lint skills: script ตรวจ SKILL.md ทุกตัว (name ตรงชื่อโฟลเดอร์, `a-z0-9-`, ≤64 ตัว, description ≤1024)
- `claude plugin validate .`
- Integration (ถ้ามี SoundCraft): `soundcraft-cli run --cmd ... --bounce` จาก smoke test
- Codex/Antigravity: ตรวจโครงสร้างไฟล์ตาม docs; การติดตั้งจริงให้ user ทดสอบ

## 8. แหล่งอ้างอิงและ License

- โปรเจกต์นี้: MIT — Copyright (c) 2026 Chaiyaporn Santangjai (`LICENSE`)
- `CREDITS.md` ระบุทุก repo ที่ได้แนวคิด พร้อม license
- นโยบาย: เขียนเนื้อหาใหม่ด้วยภาษาของเราเอง ไม่ copy ข้อความยาว; ถ้าดัดแปลงข้อความจาก repo MIT ให้คง copyright notice ใน `CREDITS.md`

| Repo | License | สิ่งที่นำมา |
|---|---|---|
| Goldwaterfung/Stratawright | MIT | preflight/read-state, exact-name lookup, error recovery classes, analyze→fix→re-analyze |
| Korben00/ableton-producer-skills | MIT | โครง SKILL.md, brief→parameters, validate-before-write, harmony/rhythm/humanize rules |
| bitwize-music-studio/claude-ai-music-skills | CC0-1.0 | gated FAIL/WARN, confirm-style questions, cross-harness manifest ตัวอย่าง, เป้า LUFS (v2) |
| rtmalikian/tech-house-production-skills | ไม่มีไฟล์ LICENSE | แนวคิดเท่านั้น: generate→measure→adjust ≤3 รอบ, ตัวเลข tech house (v2) |
| glincker/ableton-skills | MIT | voicing ตามช่วงเครื่องดนตรี, groove-builder |
| kennethreitz/pytheory | MIT | อ้างอิง logic ทฤษฎี (ตรวจผล parser) |
| dreamrec/LivePilot | BSL-1.1 | แนวคิดเท่านั้น: User Corpus |

**Backlog ความรู้สำหรับ v2:** gain staging/LUFS targets/EQ-comp tables (tech-house, bitwize) → mix-assist;
arrangement templates + "ทุก 8 ห้องต้องมีอะไรเปลี่ยน" → song-sketch; bassline/topline rules (Korben) → bassline/melody

## 9. แผนต้นทุน (การ implement)

งานย่อยที่ไม่ต้องตัดสินใจเชิงออกแบบ (คลัง genres/grooves, free-plugins, tests, README, manifests)
มอบให้ subagent ราคาถูก (Sonnet 5.5 / Haiku 5.5 / GPT ผ่าน T3) — งาน core (theory, midi_writer, spec)
และการรีวิวทำโดย model หลัก

## 10. Roadmap

| Phase | Skills | ต้องการจาก phase ก่อน |
|---|---|---|
| **1** (spec นี้) | soundcraft-core, soundcraft-setup, chords, drums, plugins, sound-design, theory-coach, thai-flavor | — |
| **2** | bassline-melody, groove-humanize, session-template, reference-brief | theory.py, midi_reader, corpus, MCP flow ที่ใช้ได้จริง |
| **3** | song-sketch, mix-assist, export-delivery, producer-next-step | ทุก skill ของ phase 1–2 + ความรู้ mix/LUFS ใน backlog §8 |

- **bassline-melody**: เบสตามคอร์ด (R/5/8 rhythm templates, "kick คุมจังหวะลง เบสคุม off-beat"), topline (chord tone บนจังหวะหนัก, phrase 2/4 ห้อง, call-response)
- **groove-humanize**: ใส่ swing/humanize/feel ให้ MIDI ที่มีอยู่ (`midi_reader` → แปลง → เขียนใหม่)
- **session-template**: สร้าง session ตามแนวในคำสั่งเดียว (tempo, tracks, instruments, buses, FX พื้นฐาน)
- **reference-brief**: ชื่อเพลง/ศิลปินอ้างอิง → style profile (BPM, key, groove, palette) ส่งต่อ skill อื่น — ไม่ดาวน์โหลดหรือวิเคราะห์ไฟล์เสียงที่มีลิขสิทธิ์
- **song-sketch**: โครงเพลงทั้งเพลง (intro/verse/chorus/drop) รวม chords+drums+bass, กฎ "ทุก 8 ห้องต้องมีอะไรเปลี่ยน"
- **mix-assist**: bounce → LUFS/peak → แนะนำ/ปรับ eq_7band/compressor ทีละขั้น วัดซ้ำ
- **export-delivery**: bounce master + stems, เป้า LUFS ตามแพลตฟอร์ม (streaming -14 / club ~-8), export MIDI
- **producer-next-step**: อ่าน session แล้วแนะนำขั้นต่อไป ("ยังไม่มีเบส", "chorus ยังไม่ต่างจาก verse")
