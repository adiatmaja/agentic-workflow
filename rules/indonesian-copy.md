# Writing Bahasa Indonesia: copy that sells, not a translated manual

**User ruling 2026-10-18**: applies to ANY Indonesian text you write: UI labels, captions, video, docs,
messages. Unscoped because language is not a file path. Sources fetched 2026-10-18 (Badan Bahasa EYD V
`ejaan.kemendikdasmen.go.id`, KBBI, PASTI term base `pasti.kemendikdasmen.go.id`, Netflix Indonesian style
guide, Glints/BINUS/UNAIR copywriting guides). The old `*.kemdikbud.go.id` hosts are dead.

**The failure this prevents**: "Isi otomatis menghitung yang muat: 33 panel", "Gambar lahan tambahan sendiri",
"Layout hasil kompilasi", "rugi setahun 7,60 %", "Putuskan layak survei". They read like a button manual and
machine translation. Better: "Kapasitas lahan langsung terhitung: 33 panel.", "Perluas area ke lahan atau atap
sekitar.", "Uji kelayakan survei dari meja, sebelum tim ke lapangan."

## Write it

- **Benefit first, never the UI mechanic.** Say what the reader GETS, then the number. Leave button names out of
  selling copy (FAB: end on the benefit). Strong openers: *Cukup …, Langsung …, Pastikan …, Perluas …*.
- **Register**: B2B/corporate/BUMN readers get **Anda** (always capital A) or no pronoun (verb-first captions).
  Never *kamu* for them (KBBI: intimate). Not stiff-formal either: copy is not an essay.
- **No calques**: never *di mana / yang mana / dalam mana* as a relative pronoun (use *yang* or rebuild);
  active voice for instructions; cut *melakukan + noun* (*membayar*, not *melakukan pembayaran*).
- **Word choice**: no colloquial words in corporate copy (*yang muat*, *sendiri*, *jalan*); no money-loss words
  in selling copy (*rugi* reads as financial loss; say *susut*, or lead with the gain); no grammar shortcuts
  (*putuskan layak survei* → *uji kelayakan survei*).
- **English terms** only when no common Indonesian one exists; check PASTI first (*unggah, unduh, tata letak,
  umpan balik, survei*). Italicise foreign words in prose; never brand names. Never *di-upload*: use *diunggah*.
  A term the client or the app already uses (e.g. a product's own feature names, *output*) stays, so that one thing keeps one name.
- **Rhythm**: vary sentence shapes. Never three lines in a row of the same pattern (especially *X: Y*). One term
  per action across the whole surface.
- **Length**: video/UI captions ≤ 42 characters per line, ≤ 2 lines (1 preferred), ≤ 17 characters per second.

## EYD V mechanics that go wrong

- Decimal comma, thousands dot (*12,5*, *13.000*); *Rp5.000* (no space); *7 persen* in running text.
- Never open a sentence with a numeral (*Sebanyak 33 panel …*).
- *di/ke/dari* as prepositions apart (*di lahan*), as affixes joined (*dijual*); *-nya* joined.
- Titles: capitalise every word except non-initial function words (*di, ke, dari, dan, yang, untuk*).

## Before shipping

1. Each line names a gain, not a button? 2. *Anda* or no pronoun? 3. No *di mana/yang mana*? 4. Every English
word checked in PASTI? 5. No *rugi* in selling copy? 6. No three lines of one shape? 7. Within the length limits?
8. Numbers in Indonesian notation? 9. For copy that sells (promo, landing page, client-facing): get a second
opinion before shipping. A different model (`agy -p … --model gemini-3.8-flash-medium`, review only, user ruling 2026-10-18) or a native reader
reads every line; rewrite each line they stumble on. **Re-run it whenever a line's CONTEXT changes, not only its words**
(user ruling 2026-10-18): a beat moved, reordered or given a new purpose, an approved line reused somewhere else, or a
re-shot frame. An approved line in a new place is unreviewed copy. Send the stills too, so the review covers the
typography. The review runs BEFORE the take is installed or the copy is reported done, never after the user asks.
