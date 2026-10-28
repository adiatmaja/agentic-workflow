#!/usr/bin/env bash
# Export the portable parts of ~/.claude to a directory + tarball.
#
#   ./export-config.sh [DEST]              # default DEST: ~/claude-config-export
#   INCLUDE_MEMORY=1 ./export-config.sh    # also carry per-project auto-memory
#   ./export-config.sh --flat              # ALSO emit PORTABLE.md, one paste-able file
#   ./export-config.sh --flat --memory C--working-space-mtel-mockup
#
# TWO DESTINATIONS, TWO ARTIFACTS.
#   the tarball    -> another CLAUDE CODE install. Unpack over ~/.claude. Keeps
#                     the directory shape, so hooks/agents/commands still work.
#   PORTABLE.md    -> a DIFFERENT harness (Codex, Gemini CLI, OpenCode, Cursor).
#                     Those read ONE instruction file and ignore ~/.claude
#                     entirely, so the rules must be flattened into it.
#
# ALLOWLIST, not denylist. A new cache/telemetry directory appearing in ~/.claude
# must never silently end up in an export. Anything not named below is excluded.
set -euo pipefail

SRC="$HOME/.claude"
DEST=""
FLAT=0
FLAT_MEMORY=""
TARGET=

while [ $# -gt 0 ]; do
  case "$1" in
    --flat)   FLAT=1; shift ;;
    --target) TARGET="${TARGET:+$TARGET,}${2:-}"; shift 2 ;;
    --memory) FLAT_MEMORY="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *)        DEST="$1"; shift ;;
  esac
done
DEST="${DEST:-$HOME/claude-config-export}"
STAMP="$(date +%Y%m%d)"
OUT="$DEST/claude-config-$STAMP"

# --- what travels -----------------------------------------------------------
FILES=(CLAUDE.md RTK.md settings.json keybindings.json)
DIRS=(rules agents commands hooks skills output-styles)

# --- what must NEVER travel (asserted after staging, not just omitted) -------
FORBIDDEN=(.credentials.json .claude.json settings.local.json CLAUDE.local.md)

rm -rf "$OUT"
mkdir -p "$OUT"

for f in "${FILES[@]}"; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$OUT/" && echo "  file  $f"
done

for d in "${DIRS[@]}"; do
  if [ -d "$SRC/$d" ]; then
    # .bak-* dirs are local snapshots, not config
    cp -r "$SRC/$d" "$OUT/" && echo "  dir   $d/"
  fi
done

# Per-project auto-memory: small, high value, but may quote private repo detail.
if [ "${INCLUDE_MEMORY:-0}" = "1" ]; then
  for m in "$SRC"/projects/*/memory; do
    [ -d "$m" ] || continue
    proj="$(basename "$(dirname "$m")")"
    mkdir -p "$OUT/memory/$proj"
    cp -r "$m/." "$OUT/memory/$proj/" && echo "  mem   $proj"
  done
fi

# --- the flat, paste-able single file ---------------------------------------
# Built from the STAGED tree, so it inherits the allowlist above and is covered
# by the secret scan below.
if [ "$FLAT" = "1" ]; then
  P="$OUT/PORTABLE.md"
  {
    echo "# Portable agent configuration"
    echo
    echo "Exported $(date -u '+%Y-%m-%d %H:%MZ') from \`~/.claude\` on \`$(hostname)\`."
    echo "Paste the whole file into the destination harness's GLOBAL instruction file."
    echo
    echo "Frontmatter is gone on purpose: only Claude Code reads \`paths:\`, so each"
    echo "scoped rule now states its scope in prose. **A rule whose \"Applies to\" line"
    echo "names globs your project does not contain is dead weight -- delete it rather"
    echo "than pasting it.**"
    echo
    echo '---'
    echo

    if [ -f "$OUT/CLAUDE.md" ]; then
      echo "## Global instructions (was ~/.claude/CLAUDE.md)"; echo
      awk -f "$SRC/flatten.awk" "$OUT/CLAUDE.md"
      echo
    fi

    if [ -f "$OUT/RTK.md" ]; then
      echo "## Machine-local tooling note (was ~/.claude/RTK.md)"; echo
      echo "> MACHINE-SPECIFIC. Describes a hook installed on the exporting machine."
      echo "> Drop this section unless that hook is installed on the target too."; echo
      awk -f "$SRC/flatten.awk" "$OUT/RTK.md"; echo
    fi

    # Unscoped rule first -- it is the one that applies to every session.
    if [ -f "$OUT/rules/workflow.md" ]; then
      echo "## Session workflow (was ~/.claude/rules/workflow.md -- applies always)"; echo
      awk -f "$SRC/flatten.awk" "$OUT/rules/workflow.md"; echo
    fi

    for r in "$OUT"/rules/*.md "$OUT"/rules/*/*.md; do
      [ -f "$r" ] || continue
      case "$r" in */workflow.md) continue ;; esac
      rel="${r#$OUT/}"
      echo "## ${rel}"; echo
      awk -f "$SRC/flatten.awk" "$r"; echo
    done

    if [ -n "$FLAT_MEMORY" ]; then
      idx="$SRC/projects/$FLAT_MEMORY/memory/MEMORY.md"
      if [ -f "$idx" ]; then
        echo "## Project memory index -- $FLAT_MEMORY"; echo
        echo "> The INDEX only. The individual memory files it links are not inlined"
        echo "> (they run to megabytes); copy the \`memory/\` directory separately if"
        echo "> the target harness can read files, and drop the links if it cannot."; echo
        cat "$idx"; echo
      else
        echo "ABORT: no memory index at $idx" >&2; exit 1
      fi
    fi

    echo '---'
    echo
    echo "## Not in this file, and why"
    echo
    echo "- **Sub-agents, slash commands, hooks, skills** -- executable harness machinery,"
    echo "  not instructions. They have no equivalent to paste into. They are in the"
    echo "  tarball beside this file; port them per-harness or drop them."
    echo "- **Credentials, MCP config, transcripts, caches.** Never exported."
    echo "- **Project CLAUDE.md files.** Those live in their own repos and travel with them."
  } > "$P"
  echo "  flat  PORTABLE.md ($(wc -c < "$P") B)"
  # Size breakdown, so trimming is informed rather than guessed. A foreign
  # harness pays for this file on EVERY turn -- the language rule sets are the
  # bulk of it and only one language is usually live.
  echo "        of which:"
  for r in "$OUT"/CLAUDE.md "$OUT"/RTK.md "$OUT"/rules/*.md "$OUT"/rules/*/*.md; do
    [ -f "$r" ] && printf "        %7s B  %s
" "$(wc -c < "$r")" "${r#$OUT/}"
  done
fi

# --- the one rule-splitting builder, shared by every harness target ----------
# The split is by the source's OWN frontmatter, measured not guessed:
#   no `paths:` globs  -> always applies -> the global instruction file
#   has `paths:` globs -> conditional    -> one skill, loaded on demand
# Every harness here (Codex, Gemini CLI, Antigravity) reads the SAME SKILL.md
# shape -- `name` + `description` frontmatter -- verified against a skill each
# already had installed. So only the destination and the install step differ.
emit_rules_set() {
  C="$1"
  mkdir -p "$C/skills"
  {
    echo "# Global agent instructions"
    echo
    echo "Ported from \`~/.claude\` on $(date -u '+%Y-%m-%d'). Rules that apply only to"
    echo "certain file types are NOT here -- they are skills, loaded on demand."
    echo
    for f in "$OUT/CLAUDE.md" "$OUT"/rules/*.md; do
      [ -f "$f" ] || continue
      [ -n "$(awk -v mode=globs -f "$SRC/flatten.awk" "$f")" ] && continue   # scoped -> skill
      echo '---'; echo
      awk -v mode=body -f "$SRC/flatten.awk" "$f"; echo
    done
  } > "$C/AGENTS.md"

  # PASS 1 -- names only. A cross-reference cannot be rewritten before every
  # target has its final name, and the top-level Python rules only get their
  # `python-` prefix here, from their OWN globs. Without it `coding-style` sits
  # beside `php-coding-style` and reads as the generic one.
  : > "$C/.names"
  for f in "$OUT"/rules/*.md "$OUT"/rules/*/*.md; do
    [ -f "$f" ] || continue
    globs="$(awk -v mode=globs -f "$SRC/flatten.awk" "$f")"
    [ -n "$globs" ] || continue
    rel="${f#$OUT/rules/}"; name="$(echo "${rel%.md}" | tr '/' '-')"
    case "$rel" in
      */*) ;;                                  # already language-foldered
      *) pfx=""
         case "$globs" in
           *'*.py'*)  pfx=python ;;
           *'*.php'*) pfx=php ;;
           *'*.ts'*)  pfx=typescript ;;
         esac
         # `python-env` already carries the language: prefixing blind yields
         # `python-python-env`.
         case "$name" in
           "$pfx"-*|"$pfx") ;;
           *) [ -n "$pfx" ] && name="$pfx-$name" ;;
         esac ;;
    esac
    printf '%s\t%s\t%s\n' "$rel" "$name" "$globs" >> "$C/.names"
  done

  # PASS 2 -- emit. Eleven rules point at `../common/<x>.md`, a directory that
  # does NOT exist in ~/.claude/rules: the links dangle at the source. A path is
  # meaningless between skills anyway, so each becomes the sibling skill's NAME.
  while IFS="$(printf '\t')" read -r rel name globs; do
    f="$OUT/rules/$rel"
    title="$(awk -v mode=body -f "$SRC/flatten.awk" "$f" | grep -m1 '^# ' | sed 's/^# //')"
    mkdir -p "$C/skills/$name"
    {
      echo '---'
      echo "name: $name"
      # The description is the ONLY part of a skill always in context, so it
      # carries the globs: that is what the model matches the task on.
      echo "description: ${title:-$name}. Use when working on files matching: $globs"
      echo '---'
      echo
      awk -v mode=body -f "$SRC/flatten.awk" "$f"
    } > "$C/skills/$name/SKILL.md.tmp"

    # A sed SCRIPT FILE, not -e args: the replacement text contains spaces and
    # would be word-split into separate arguments, which fails as an
    # "unterminated s command" rather than as anything that names the cause.
    : > "$C/.sedscript"
    while IFS="$(printf '\t')" read -r r2 n2 g2; do
      case "$r2" in */*) continue ;; esac      # only top-level rules were "common/"
      base="${r2%.md}"
      printf 's|\[common/%s\.md\](\.\./common/%s\.md)|the `%s` skill|g\n' \
        "$base" "$base" "$n2" >> "$C/.sedscript"
    done < "$C/.names"
    sed -f "$C/.sedscript" "$C/skills/$name/SKILL.md.tmp" > "$C/skills/$name/SKILL.md"
    rm -f "$C/skills/$name/SKILL.md.tmp"
  done < "$C/.names"
  rm -f "$C/.names" "$C/.sedscript"
}

# --- target: codex ----------------------------------------------------------
# NOT the flat file. Codex has a real skills system, so pasting every rule into
# AGENTS.md would charge always-on tokens for a PHP rule during a Python task.
# The split is by the source's OWN frontmatter, measured not guessed:
#
#   no `paths:` globs -> always applies -> AGENTS.md
#   has `paths:` globs -> conditional  -> one skill, loaded on demand
#
# MEASURED on codex 0.143.0, this machine, 2026-09-09:
#   * `~/.codex/AGENTS.md` is read, and is prepended to the project AGENTS.md
#     inside ONE block separated by `--- project-doc ---`.
#   * That whole block is capped by `project_doc_max_bytes`, default 32768,
#     and the overflow is cut MID-WORD with no warning anywhere. Global text
#     therefore evicts the tail of every project's own instructions.
#   * `~/.codex/skills/<name>/SKILL.md` loads. So do `~/.agents/skills/` and
#     `<repo>/.agents/skills/`. All three were confirmed by marker skill.
# Re-derive any of it with:  codex debug prompt-input
case ",$TARGET," in *,codex,*) ;; *) false ;; esac && {
  C="$OUT/codex"
  emit_rules_set "$C"

  AG=$(wc -c < "$C/AGENTS.md")
  cat > "$C/config-additions.toml" <<TOML
# Append to ~/.codex/config.toml.
#
# REQUIRED, not a preference. MEASURED on codex 0.143.0: the default caps the
# PROJECT doc at 32768 bytes and cuts it MID-WORD with no warning anywhere. The
# global file ($AG B here) is prepended on top of that and is not itself capped.
# Verify the result with: codex debug prompt-input
project_doc_max_bytes = 262144
TOML

  cat > "$C/install.sh" <<'INST'
#!/usr/bin/env bash
# Install this export into Codex. Run from the directory holding it.
set -euo pipefail
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

# AGENTS.override.md, if it exists, makes AGENTS.md invisible -- silently.
if [ -f "$CODEX_HOME/AGENTS.override.md" ]; then
  echo "REFUSING: $CODEX_HOME/AGENTS.override.md exists and suppresses AGENTS.md." >&2
  echo "Remove or merge it first." >&2; exit 1
fi
[ -f "$CODEX_HOME/AGENTS.md" ] && cp "$CODEX_HOME/AGENTS.md" "$CODEX_HOME/AGENTS.md.bak"
[ -f "$CODEX_HOME/config.toml" ] && cp "$CODEX_HOME/config.toml" "$CODEX_HOME/config.toml.bak"

mkdir -p "$CODEX_HOME/skills"
cp AGENTS.md "$CODEX_HOME/AGENTS.md"
cp -r skills/. "$CODEX_HOME/skills/"

# Appending a key TOML already holds is a duplicate-key parse error, which
# breaks every codex invocation -- so this must be idempotent, not just correct
# on a clean machine.
if grep -qE '^[[:space:]]*project_doc_max_bytes' "$CODEX_HOME/config.toml" 2>/dev/null; then
  echo "note: project_doc_max_bytes already set -- left as it is:"
  grep -nE '^[[:space:]]*project_doc_max_bytes' "$CODEX_HOME/config.toml"
else
  # A bare key APPENDED to a TOML file belongs to the last table header above
  # it -- here `[plugins."..."]`. Codex accepts the file, ignores the setting,
  # and warns about nothing; the only symptom is a project doc still truncated.
  # Top-level keys go BEFORE the first table header.
  T="$CODEX_HOME/config.toml.new"
  awk -v add="config-additions.toml" '
    !done && /^[[:space:]]*\[/ {
      while ((getline line < add) > 0) print line
      print ""
      done = 1
    }
    { print }
    END { if (!done) { while ((getline line < add) > 0) print line } }
  ' "$CODEX_HOME/config.toml" > "$T"
  mv "$T" "$CODEX_HOME/config.toml"
fi

echo "Installed. VERIFY -- do not assume:"
echo "  codex debug prompt-input | grep -c 'project-doc'"
echo "Then check the AGENTS.md block is not truncated: its last line must be"
echo "the real end of your project doc, not a half-word."
INST
  chmod +x "$C/install.sh"
  echo "  codex AGENTS.md ($AG B) + $(ls "$C/skills" | wc -l) skills"
}

# --- target: gemini (Gemini CLI) --------------------------------------------
# VERIFIED against the shipped bundle, not the docs: `settings.context.fileName`
# is the live key (the flat `contextFileName` also appears but the v2 nested one
# is what `setGeminiMdFilename()` reads). It accepts a string or an array and
# REPLACES the default, so GEMINI.md must stay in the list or Gemini CLI stops
# reading its own file. Gemini CLI does NOT read AGENTS.md without this.
case ",$TARGET," in *,gemini,*) ;; *) false ;; esac && {
  C="$OUT/gemini"
  emit_rules_set "$C"
  mv "$C/AGENTS.md" "$C/GEMINI.block.md"

  cat > "$C/settings-additions.json" <<'JSON'
{
  "context": {
    "fileName": ["GEMINI.md", "AGENTS.md", "CLAUDE.md"]
  }
}
JSON

  cat > "$C/install.sh" <<'INST'
#!/usr/bin/env bash
# Install this export into Gemini CLI. Run from the directory holding it.
set -euo pipefail
GEM="${GEMINI_HOME:-$HOME/.gemini}"
mkdir -p "$GEM/skills"

# ~/.gemini/GEMINI.md is WRITTEN BY THE TOOL -- `/memory add` appends "## Gemini
# Added Memories" there. Overwriting it destroys the user's own memories, so the
# ported rules go in a delimited block that a re-run REPLACES rather than
# duplicates. Anything outside the markers is left exactly as it was.
BEGIN='<!-- BEGIN ported from ~/.claude -- do not edit inside these markers -->'
END='<!-- END ported from ~/.claude -->'
touch "$GEM/GEMINI.md"
cp "$GEM/GEMINI.md" "$GEM/GEMINI.md.bak"
awk -v b="$BEGIN" -v e="$END" '
  $0==b {skip=1} !skip {print} $0==e {skip=0}
' "$GEM/GEMINI.md" > "$GEM/GEMINI.md.keep"
{ printf '%s
' "$(cat "$GEM/GEMINI.md.keep")"; echo "$BEGIN"; cat GEMINI.block.md; echo "$END"; } > "$GEM/GEMINI.md"
rm -f "$GEM/GEMINI.md.keep"

cp -r skills/. "$GEM/skills/"

# settings.json is a real JSON document with the user's model config in it --
# merge, never clobber, and never hand-edit with sed.
cp "$GEM/settings.json" "$GEM/settings.json.bak" 2>/dev/null || true
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" - "$GEM/settings.json" settings-additions.json <<'PYEOF'
import json, sys, io, os
target, add = sys.argv[1], sys.argv[2]
cur = {}
if os.path.exists(target):
    cur = json.load(io.open(target, encoding='utf-8'))
new = json.load(io.open(add, encoding='utf-8'))
ctx = cur.setdefault('context', {})
want = new['context']['fileName']
have = ctx.get('fileName')
have = [have] if isinstance(have, str) else (have or [])
# GEMINI.md must survive: this key REPLACES the default filename, it does not
# extend it, so dropping it would silently stop the global file being read.
merged = list(dict.fromkeys(['GEMINI.md'] + have + want))
ctx['fileName'] = merged
io.open(target, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(cur, indent=2, ensure_ascii=False) + '\n')
print('context.fileName =', merged)
PYEOF

echo "Installed. VERIFY -- no context dump exists, so probe the live model:"
echo "  gemini -p 'Reply with only the word inside the marker in your instructions.'"
INST
  chmod +x "$C/install.sh"
  echo "  gemini GEMINI.block.md ($(wc -c < "$C/GEMINI.block.md") B) + $(ls "$C/skills" | wc -l) skills"
}

# --- target: antigravity (agy) ----------------------------------------------
# Antigravity and Gemini CLI SHARE ~/.gemini but read DIFFERENT global files:
# Gemini CLI takes ~/.gemini/GEMINI.md, Antigravity takes ~/.gemini/config/AGENTS.md
# (and keeps its skills in ~/.gemini/config/skills/, a separate tree from
# ~/.gemini/skills/ -- both held their own copy of the same skill on this
# machine, with different frontmatter). Installing one does NOT configure the
# other, which is why this is a separate target rather than a flag.
case ",$TARGET," in *,antigravity,*|*,agy,*) ;; *) false ;; esac && {
  C="$OUT/antigravity"
  emit_rules_set "$C"

  cat > "$C/install.sh" <<'INST'
#!/usr/bin/env bash
# Install this export into Antigravity (agy). Run from the directory holding it.
set -euo pipefail
AG="${ANTIGRAVITY_HOME:-$HOME/.gemini/config}"
mkdir -p "$AG/skills"

# Same reason as Gemini CLI: this file already holds tool-written
# "## Gemini Added Memories". Delimited block, replaced on re-run.
BEGIN='<!-- BEGIN ported from ~/.claude -- do not edit inside these markers -->'
END='<!-- END ported from ~/.claude -->'
touch "$AG/AGENTS.md"
cp "$AG/AGENTS.md" "$AG/AGENTS.md.bak"
awk -v b="$BEGIN" -v e="$END" '
  $0==b {skip=1} !skip {print} $0==e {skip=0}
' "$AG/AGENTS.md" > "$AG/AGENTS.md.keep"
{ printf '%s
' "$(cat "$AG/AGENTS.md.keep")"; echo "$BEGIN"; cat AGENTS.md; echo "$END"; } > "$AG/AGENTS.md"
rm -f "$AG/AGENTS.md.keep"

cp -r skills/. "$AG/skills/"

echo "Installed into $AG. VERIFY -- probe the live model:"
echo "  agy -p 'Reply with only the word inside the marker in your instructions.'"
INST
  chmod +x "$C/install.sh"
  echo "  antigravity AGENTS.md ($(wc -c < "$C/AGENTS.md") B) + $(ls "$C/skills" | wc -l) skills"
}

# --- guard 1: no forbidden filename anywhere in the staged tree --------------
for bad in "${FORBIDDEN[@]}"; do
  if find "$OUT" -name "$bad" -print -quit | grep -q .; then
    echo "ABORT: $bad reached the export tree" >&2; exit 1
  fi
done

# --- guard 2: scan staged bytes for credential-shaped strings ---------------
# Catches a key pasted into a rules/ or agents/ file, which the filename
# allowlist cannot see. Reports and aborts rather than shipping quietly.
#
# Patterns require REAL key lengths on purpose. Matching a bare field name
# ("access_token") or a placeholder (ghp_xxxx, sk-ant-...) fires on every
# security doc and code sample you own; a guard that cries wolf gets bypassed,
# and a bypassed guard is worse than no guard.
SECRET_RE='(sk-ant-[A-Za-z0-9_-]{20,}'
SECRET_RE+='|ghp_[A-Za-z0-9]{36}'
SECRET_RE+='|github_pat_[A-Za-z0-9_]{40,}'
SECRET_RE+='|AKIA[0-9A-Z]{16}'
SECRET_RE+='|-----BEGIN [A-Z ]*PRIVATE KEY-----'
SECRET_RE+='|"(access|refresh)_token"[[:space:]]*:[[:space:]]*"[A-Za-z0-9._-]{20,}")'

if grep -rIlE "$SECRET_RE" "$OUT" 2>/dev/null | grep . ; then
  echo "ABORT: credential-shaped string found in the files listed above." >&2
  echo "Inspect with:  grep -nE '$SECRET_RE' <file>" >&2
  echo "Scrub them, then re-run. (Nothing was archived.)" >&2
  exit 1
fi

tar -czf "$OUT.tar.gz" -C "$DEST" "claude-config-$STAMP"

echo
echo "Exported to: $OUT"
echo "Tarball:     $OUT.tar.gz  ($(du -h "$OUT.tar.gz" | cut -f1))"
[ "$FLAT" = "1" ] && echo "Paste file:  $OUT/PORTABLE.md"
echo
echo "NOT included, by design: .credentials.json (auth token), ~/.claude.json"
echo "(MCP config + project history), projects/ transcripts, plugins/ cache,"
echo "file-history/, history.jsonl, paste-cache/, telemetry/, shell-snapshots/."
echo "Plugins reinstall from settings.json's enabledPlugins + extraKnownMarketplaces."
