#!/usr/bin/env bash
# One-command check that the 2026-09-19 token-reduction setup is still in force.
# Run from any project after installing into ~/.claude:  bash tools/verify-setup.sh
# Every line prints PASS or FAIL with the measured value - never "looks fine".
fail=0
chk(){ if [ "$2" = "$3" ]; then printf "PASS  %-34s %s\n" "$1" "$2"; else printf "FAIL  %-34s got '%s' want '%s'\n" "$1" "$2" "$3"; fail=1; fi; }

v=$(python -c "import json;print(json.load(open(r'$HOME/.claude/settings.json'.replace('/c/','C:/'),encoding='utf-8')).get('autoCompactWindow'))" 2>/dev/null \
   || python -c "import json,os;print(json.load(open(os.path.expanduser('~/.claude/settings.json'),encoding='utf-8')).get('autoCompactWindow'))")
chk "autoCompactWindow" "$v" "300000"

v=$(python -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json'),encoding='utf-8'));
b=[h for h in d['hooks']['PreToolUse'] if h.get('matcher')=='Bash'][0];
print(sum(1 for x in b['hooks'] if 'node-test-compact' in (x.get('command') or '')))")
chk "node-test hook registered" "$v" "1"

v=$(echo '{"tool_name":"Bash","tool_input":{"command":"node --test x.mjs"}}' \
    | python "$HOME/.claude/hooks/node-test-compact.py" | grep -c "updatedInput")
chk "node-test hook rewrites" "$v" "1"

# A COMPOUND line must compact too, and `$?` after it must be the runner's. Executes the
# rewrite: before 2026-09-19's fix the redirect bound only to the trailing `echo`, and the
# full output leaked. Pass = summary present, no per-test line, status carried through.
_t=$(mktemp -d); printf 'const t=require("node:test");for(let i=0;i<20;i++)t.test("t"+i,()=>{});\n' > "$_t/a.test.js"
printf 'const t=require("node:test");t.test("bad",()=>{throw new Error("x")});\n' > "$_t/b.test.js"
_run() { python -c 'import json,sys;print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1" \
    | python "$HOME/.claude/hooks/node-test-compact.py" \
    | python -c 'import json,sys;print(json.load(sys.stdin)["hookSpecificOutput"]["updatedInput"]["command"])' \
    | (cd "$_t" && bash) 2>&1; }
o=$(_run 'node --test a.test.js; echo "RC=$?"')
case "$o" in *"✔"*) r=leaked;; *"pass 20"*"RC=0"*) r=ok;; *) r=bad;; esac
chk "node-test compound compacts" "$r" "ok"
o=$(_run 'node --test b.test.js; echo "RC=$?"')
case "$o" in *"fail 1"*"RC=1"*) r=ok;; *) r=bad;; esac
chk "node-test compound keeps status" "$r" "ok"
rm -rf "$_t"

v=$(python -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json'),encoding='utf-8'));print(sum(1 for m in d['hooks']['PreToolUse'] for h in m['hooks'] if 'rtk' in h.get('command','') or 'serena' in h.get('command','')))")
chk "no rtk/serena hooks (removed 09-23)" "$v" "0"

v=$(grep -c "cacheTtl: 1h" "$HOME/.claude/agents/plan-orchestrator.md")
chk "plan-orchestrator 1h cache" "$v" "1"

v=$(grep -l "cacheTtl: 1h" "$HOME"/.claude/agents/impl-sonnet-*.md "$HOME"/.claude/agents/impl-opus-*.md 2>/dev/null | wc -l | tr -d ' ')
chk "implementers 1h cache (trial 2026-10-10)" "$v" "5"

v=$(grep -l "^omitClaudeMd: true" "$HOME"/.claude/agents/review-*.md "$HOME/.claude/agents/code-reviewer.md" "$HOME/.claude/agents/audit-visual.md" 2>/dev/null | wc -l | tr -d ' ')
chk "reviewers omit CLAUDE.md" "$v" "5"

v=$(python -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json'),encoding='utf-8'));print(sum(1 for m in d['hooks']['PreToolUse'] if m.get('matcher')=='Read' for h in m['hooks'] if 'read-guard' in h.get('command','')))")
chk "read-guard hook registered" "$v" "1"
# Behaviour, not presence: fixtures it writes itself; also asserts every outline range is exact.
PYTHONIOENCODING=utf-8 python "$HOME/.claude/hooks/read-guard.test.py" >/dev/null 2>&1; chk "read-guard refuses + outlines" "$?" "0"


v=$(grep -c "^model: sonnet" "$HOME/.claude/agents/audit-visual.md")
chk "audit-visual on sonnet (2026-10-17)" "$v" "1"
v=$(grep -c "^model: sonnet" "$HOME/.claude/agents/code-reviewer.md")
chk "code-reviewer on sonnet; review-adversarial is the Opus escalation (2026-10-17)" "$v" "1"
v=$(grep -l "Commits (owner ruling 2026-10-17" "$HOME/.claude/agents"/impl-*.md | wc -l)
chk "every impl-* agent carries the small-commit rule (2026-10-17)" "$v" "$(ls "$HOME/.claude/agents"/impl-*.md | wc -l)"
v=$(printf '{"tool_name":"Agent","tool_input":{"subagent_type":"impl-sonnet-medium"}}' | python "$HOME/.claude/hooks/agent-dispatch-guard.py" | grep -c '"deny"')
chk "dispatch guard refuses an impl-* agent without a worktree (2026-10-17)" "$v" "1"
v=$(printf '{"tool_name":"Agent","tool_input":{"subagent_type":"impl-sonnet-medium","isolation":"worktree"}}' | python "$HOME/.claude/hooks/agent-dispatch-guard.py" | grep -c '"deny"')
chk "dispatch guard allows an impl-* agent in a worktree" "$v" "0"
v=$(grep -c "using-git-worktrees" "$HOME/.claude/hooks/plan-dispatch-ruling.py")
chk "dispatch ruling injects on using-git-worktrees too (2026-10-17)" "$v" "1"

echo
if [ $fail -eq 0 ]; then echo "ALL PASS - setup intact."; else
  echo "SOMETHING REGRESSED. Re-measure with /usage."; fi
exit $fail
