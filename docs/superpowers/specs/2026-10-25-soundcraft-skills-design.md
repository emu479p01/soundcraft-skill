# SoundCraft Skills — Design Spec

- วันที่: 2026-10-25
- สถานะ: รอรีวิว
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

**นอกขอบเขต v1:** bassline/melody, song-sketch (ทั้งเพลง), mix-assist, การดาวน์โหลด/รัน installer ของ plugin อัตโนมัติ

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
│   │   │   ├── scan_plugins.py       # CLI: สแกนโฟลเดอร์ plugin -> JSON
│   │   │   └── scmidi/
│   │   │       ├── theory.py         # parse คอร์ด/เลขโรมัน, voicing, voice leading
│   │   │       ├── rhythm.py         # step string parser, swing, humanize, fill
│   │   │       ├── drums.py          # drum maps (gm, soundcraft, custom)
│   │   │       ├── spec.py           # validate JSON spec -> error ที่อ่านเข้าใจ
│   │   │       └── midi_writer.py    # เขียน SMF type 1 (stdlib ล้วน)
│   │   └── references/soundcraft-commands.md
│   ├── soundcraft-setup/SKILL.md
│   ├── chords/{SKILL.md, references/genres.md}
│   ├── drums/{SKILL.md, references/grooves.md}
│   └── plugins/{SKILL.md, references/free-plugins.md}
├── .claude-plugin/{plugin.json, marketplace.json}   # Claude Code
├── .mcp.json                                        # Claude Code + Codex
├── .codex-plugin/plugin.json                        # Codex
├── .agents/plugins/marketplace.json                 # Codex marketplace
├── plugin.json, mcp_config.json                     # Antigravity
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
- `voicing`: `close` | `open` | `drop2` | `spread`; voice leading อัตโนมัติ (เลือก inversion ที่ระยะรวมน้อยสุด) ปิดได้ด้วย `"voice_leading": false`
- `rhythm`: `block` | `pad` | `stabs` | `arp-up` | `arp-down` | `arp-updown` | `custom` (+ `"steps"` string)
- `bass_note`: `true` เพิ่ม root ต่ำ 1 octave (ค่าเริ่ม `false`)

**Drums track**
- step chars: `x` ปกติ (vel 100), `X` accent (vel 120), `g` ghost (vel 45), `.` rest
- ความยาว string = `steps` ต่อห้อง (ค่าเริ่ม 16); ยาวกว่า 1 ห้องได้ถ้าเป็นจำนวนเท่าของ `steps`
- เสียง: `kick snare clap rim hat open_hat pedal_hat ride crash tom_hi tom_mid tom_low shaker tambourine cowbell perc`
- `swing` 0.5–0.75 (เลื่อน step คี่), `humanize` 0–1 (สุ่ม timing ±/velocity ด้วย seed คงที่ — `"seed"` กำหนดได้)
- `fill.every` N ห้อง แทนที่ห้องสุดท้ายของทุก N ห้องเฉพาะเสียงที่ระบุ
- `drum_map`: `gm` | `soundcraft` | object `{"kick": 36, ...}`

**Output**
- SMF type 1, PPQ 480, tempo + time signature ใน track 0, หนึ่ง track ต่อ spec track
- กลองใช้ channel 10, คอร์ดใช้ channel 1+ ตามลำดับ
- stdout: สรุปข้อความรายห้อง (`Bar 1: Dm9 = D3 A3 C4 E4 F4`) + path ไฟล์
- `--json` ให้สรุปเป็น JSON
- Exit code: 0 สำเร็จ, 2 spec ไม่ถูกต้อง (ข้อความระบุ field + ค่า + สิ่งที่ยอมรับ)

## 5. Skills

| Skill | หน้าที่ |
|---|---|
| `soundcraft-core` | เอกสารวิธีเรียก script + คำสั่ง MCP; ใช้ตรงได้สำหรับ "export เป็น .mid" |
| `soundcraft-setup` | เช็ก/แนะนำติดตั้ง SoundCraft + Python, ตั้ง MCP ตาม harness, smoke test |
| `chords` | ตีความคำขอ → spec → import → ตั้ง instrument (ค่าเริ่ม `subtractive_synth` หรือ plugin ที่ user ระบุ) |
| `drums` | ตีความ genre/BPM/feel → spec → import → `drum_synth` หรือ plugin กลองของ user (เลือก `drum_map`) |
| `plugins` | สแกน → รายงาน → แนะนำ plugin ฟรี (เปิดหน้าดาวน์โหลด, ไม่รัน installer) → โหลดเข้า track |

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

## 8. แผนต้นทุน (การ implement)

งานย่อยที่ไม่ต้องตัดสินใจเชิงออกแบบ (คลัง genres/grooves, free-plugins, tests, README, manifests)
มอบให้ subagent ราคาถูก (Sonnet 5.5 / Haiku 5.5 / GPT ผ่าน T3) — งาน core (theory, midi_writer, spec)
และการรีวิวทำโดย model หลัก
