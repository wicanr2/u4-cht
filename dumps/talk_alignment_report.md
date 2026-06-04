# .TLK ↔ talk.json 對齊報告

> 自動產生 by `tools/extract_tlk.py`

## 摘要

- DOS `.TLK` 抽出 NPC:**256**
- u4remastered `talk.json` 條目:**256**
- 以 name 對齊成功:**250**
- 找不到對應(僅 .TLK 有):**6**
- 英文內容有差異的 NPC(remaster 修過對白 / 格式):**188**

## 無對應 NPC(DOS .TLK name 欄位異常,疑似 remaster 修過的 broken dialogue)

這些 record 的 `name` 欄位實際是描述片語,需人工依 town/index 對 talk.json 核對。

| TLK | idx | name 欄位(原始) | job |
|---|---|---|---|
| EMPATH | 3 | `Life.` | `I resonate thoughts.` |
| LYCAEUM | 9 | `a truth seeker.` | `I seek to know truth.` |
| LYCAEUM | 14 | `Nigel, at thy service.` | `I teach magical spells.` |
| SERPENT | 1 | `the gate guard.` | `Guard the gates, of course.` |
| SERPENT | 4 | `a ranger.` | `I am training!` |
| YEW | 8 | `a poor beggar.` | `I have sinned.` |

## 英文差異明細(前 40 筆)

差異多源於 u4remastered 修正對白 bug 與 C64 16-col 換行;**翻譯底本以 DOS `.TLK` 的 en 為準**(引擎實際輸出),talk.json 作參考。

### Gweno (BRITAIN)
- `keyword_1`:
    - TLK: `DANC`
    - JSON: `DANCE`

### a child (BRITAIN)
- `keyword_2`:
    - TLK: `HO E`
    - JSON: `HO EYO`

### a guard (BRITAIN)
- `description`:
    - TLK: `a guard.`
    - JSON: `a burly guard.`
- `job`:
    - TLK: `I guard the bridge.`
    - JSON: `I guard the castle and my liege!`
- `health`:
    - TLK: `Good.`
    - JSON: `Great!`
- `keyword_response_1`:
    - TLK: `Across the bridge our people dance and sing!`
    - JSON: `A guard must be a valiant warrior!`
- `keyword_response_2`:
    - TLK: `Yep.`
    - JSON: `I serve Lord British!`
- `question`:
    - TLK: `Would thou like to join them?`
    - JSON: `Art thou the most valiant warrior?`
- `question_yes_answer`:
    - TLK: `Remember, an open heart is the first step on the path to wisdom!`
    - JSON: `Then thou should be a guard!`
- `question_no_answer`:
    - TLK: `Then you have no business across the bridge.`
    - JSON: `Still flee not from battle!`
- `keyword_1`:
    - TLK: `BRID`
    - JSON: `GUAR`
- `keyword_2`:
    - TLK: `GUAR`
    - JSON: `LIEGE`

### Thevel (BRITAIN)
- `keyword_2`:
    - TLK: `MAGI`
    - JSON: `MAGIC`

### Joe (BRITAIN)
- `keyword_1`:
    - TLK: `STON`
    - JSON: `STONE`

### Cricket (BRITAIN)
- `keyword_2`:
    - TLK: `MANT`
    - JSON: `MANTRA`

### a guard (BRITAIN)
- `description`:
    - TLK: `a cheerful guard.`
    - JSON: `a burly guard.`
- `job`:
    - TLK: `I am a guard of course!`
    - JSON: `I guard the castle and all within.`
- `health`:
    - TLK: `I am fully healed.`
    - JSON: `Couldn't be better!`
- `keyword_response_1`:
    - TLK: `We guards have a lot of compassion.`
    - JSON: `I guard the castle!`
- `keyword_response_2`:
    - TLK: `We always say: Let all others' troubles be as thine own!`
    - JSON: `The castle is fair and strong!`
- `question`:
    - TLK: `Dost thou kill non-evil creatures?`
    - JSON: `Do you seek Lord British?`
- `question_yes_answer`:
    - TLK: `That does not show compassion!`
    - JSON: `He is on the upper level in the throne room.`
- `question_no_answer`:
    - TLK: `Good.`
    - JSON: `He will aid you if you are in need!`
- `keyword_1`:
    - TLK: `GUAR`
    - JSON: `GUARD`
- `keyword_2`:
    - TLK: `COMP`
    - JSON: `CAST`

### a child (BRITAIN)
- `keyword_1`:
    - TLK: `LEAR`
    - JSON: `LEARN`

### Shalimar (BRITAIN)
- `keyword_1`:
    - TLK: `CHIL`
    - JSON: `CHILD`

### Sebastian (BRITAIN)
- `keyword_1`:
    - TLK: `SECR`
    - JSON: `SECRET`

### Shapero (BRITAIN)
- `keyword_1`:
    - TLK: `JULI`
    - JSON: `JULIO`

### Julio (BRITAIN)
- `keyword_1`:
    - TLK: `NATU`
    - JSON: `NATURE`

### Mentor (BRITAIN)
- `keyword_1`:
    - TLK: `MAGI`
    - JSON: `MAGIN`
- `keyword_2`:
    - TLK: `PRID`
    - JSON: `PRIDE`

### Sprite (BRITAIN)
- `keyword_1`:
    - TLK: `STAR`
    - JSON: `STARV`

### Allen (COVE)
- `keyword_1`:
    - TLK: `ABYS`
    - JSON: `ABYSS`

### Frontis (COVE)
- `keyword_1`:
    - TLK: `WISD`
    - JSON: `WISDOM`
- `keyword_2`:
    - TLK: `PEAC`
    - JSON: `PEACE`

### Sloven (COVE)
- `keyword_1`:
    - TLK: `RECL`
    - JSON: `RECLU`
- `keyword_2`:
    - TLK: `STON`
    - JSON: `STONE`

### the ankh (COVE)
- `keyword_1`:
    - TLK: `CODE`
    - JSON: `CODEX`
- `keyword_2`:
    - TLK: `CHAM`
    - JSON: `CHAMB`

### Paul (COVE)
- `keyword_2`:
    - TLK: `PROB`
    - JSON: `PROBLE`

### Linda (COVE)
- `keyword_1`:
    - TLK: `CHIL`
    - JSON: `CHILD`
- `keyword_2`:
    - TLK: `WORL`
    - JSON: `WORLD`

### Merlin (COVE)
- `keyword_1`:
    - TLK: `STON`
    - JSON: `STONE`

### Draconian (COVE)
- `keyword_1`:
    - TLK: `RELA`
    - JSON: `RELAT`

### Blissful (COVE)
- `keyword_1`:
    - TLK: `CODE`
    - JSON: `CODEX`
- `keyword_2`:
    - TLK: `ABYS`
    - JSON: `ABYSS`

### Rabindranath
tagore (COVE)
- `keyword_2`:
    - TLK: `HEAR`
    - JSON: `HEART`

### Brother Zair (COVE)
- `keyword_1`:
    - TLK: `RIVE`
    - JSON: `RIVER`

### Spellbind (COVE)
- `keyword_1`:
    - TLK: `CODE`
    - JSON: `CODEX`

### Shaman (COVE)
- `keyword_1`:
    - TLK: `STUD`
    - JSON: `STUDY`
- `keyword_2`:
    - TLK: `CODE`
    - JSON: `CODEX`

### Charm (COVE)
- `keyword_2`:
    - TLK: `AXIO`
    - JSON: `AXIOM`

### Circe (COVE)
- `keyword_1`:
    - TLK: `AXIO`
    - JSON: `AXIOM`
- `keyword_2`:
    - TLK: `PART`
    - JSON: `PARTS`

### Roofus (DEN)
- `keyword_1`:
    - TLK: `BRID`
    - JSON: `BRIDGE`

### Rankbreath (DEN)
- `keyword_1`:
    - TLK: `GUAR`
    - JSON: `GUARD`
- `keyword_2`:
    - TLK: `HUNG`
    - JSON: `HUNGER`

### Slysam (DEN)
- `keyword_1`:
    - TLK: `THIE`
    - JSON: `THIEF`
- `keyword_2`:
    - TLK: `CLEV`
    - JSON: `CLEVER`

### Ragnar (DEN)
- `keyword_1`:
    - TLK: `TRAV`
    - JSON: `TRAVEL`
- `keyword_2`:
    - TLK: `SKUL`
    - JSON: `SKULL`

### Seanna (DEN)
- `keyword_1`:
    - TLK: `MAGI`
    - JSON: `MAGIC`
- `keyword_2`:
    - TLK: `SLEE`
    - JSON: `SLEEP`

### Starlight (DEN)
- `keyword_response_2`:
    - TLK: `Try one black pearl and one part sulfurous ash!`
    - JSON: `Try one black pearl and one part sulphurous ash!`
- `keyword_1`:
    - TLK: `MAGI`
    - JSON: `MAGIC`

### Boris (DEN)
- `keyword_1`:
    - TLK: `ITEM`
    - JSON: `ITEMS`

### Green Beard (DEN)
- `keyword_1`:
    - TLK: `ARMO`
    - JSON: `ARMOUR`
- `keyword_2`:
    - TLK: `NOWH`
    - JSON: `NOWHER`

### Marsor (DEN)
- `keyword_2`:
    - TLK: `VINT`
    - JSON: `VINTAG`

### Dancek (DEN)
- `keyword_1`:
    - TLK: `TINK`
    - JSON: `TINKER`
- `keyword_2`:
    - TLK: `MACH`
    - JSON: `MACHIN`

### Lord Robert (EMPATH)
- `question_yes_answer`:
    - TLK: `It is 'amo' seek ye now the other parts!`
    - JSON: `It is 'AMO'! Seek ye now the other parts!`
