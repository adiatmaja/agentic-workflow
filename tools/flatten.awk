# Render one ~/.claude config file for a foreign harness. Three modes:
#
#   mode=section (default) -- a section of a single flat paste file
#   mode=globs             -- print ONLY the frontmatter globs, comma-joined
#   mode=body              -- the body alone, headings left at their own level
#
# Why the transforms exist, all because the destination is NOT Claude Code:
#
# 1. Frontmatter `paths:` globs. No other harness reads them, so an unscoped
#    paste fires the rule on every file. In `section` they become an "Applies
#    to" line; in `body` the caller re-states them in its own frontmatter.
# 2. Heading demotion (`section` only) so each file nests under the header that
#    introduces it. Without it a source file's own `#` outranks that header and
#    the boundary between two rules is invisible. In `body` the file stands
#    alone and its levels are already correct.
#    Demotion is skipped inside fenced code blocks: `# comment` is Python.
# 3. `@file.md` includes are a Claude Code feature and dangle anywhere else.
#    `@decorator` inside a fence is untouched by the same fence test.
#
# The CR strip is load-bearing, not tidiness: these files are CRLF on Windows
# and every `$`-anchored rule below silently matches nothing without it -- the
# transform then reports success having changed nothing.
BEGIN { fm=0; fence=0; globs=""; if (mode == "") mode="section" }
{ sub(/\r$/, "") }
NR==1 && $0=="---" { fm=1; next }
fm==1 && $0=="---" { fm=0
  if (mode=="globs") { print globs; exit }
  if (mode=="section" && globs != "") printf "**Applies to:** %s\n\n", globs
  next }
fm==1 {
  if (match($0, /"[^"]+"/)) {
    g = substr($0, RSTART+1, RLENGTH-2)
    globs = (globs == "" ? g : globs ", " g)
  }
  next
}
mode=="globs" { exit }                      # no frontmatter at all -> empty
/^[ \t]*(```|~~~)/ { fence = !fence; print; next }
!fence && /^@[A-Za-z0-9_.\/-]+$/ { next }
!fence && mode=="section" && /^#{1,4} / { print "##" $0; next }
{ print }
END { if (mode=="globs" && fm==1) print globs }
