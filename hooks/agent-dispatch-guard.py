#!/usr/bin/env python
"""PreToolUse hook on Agent: every dispatch must name a CONFIGURED agent and must not override its model.

User ruling 2026-09-14: "must always use configured agent when dispatching an agent." A configured
agent is one defined in ~/.claude/agents/*.md or <project>/.claude/agents/*.md (or a plugin's
agents/*.md, addressed as "plugin:name"). Those files carry model + effort, so a dispatch that omits
subagent_type (general-purpose by default), picks a built-in (Explore, Plan, fork, ...) or passes
`model` would silently bypass the tiering. The deny reason lists the live names, so it cannot go stale.

Fails OPEN on any internal error: a bug here must never make every dispatch impossible.
"""

import glob
import json
import os
import re
import sys

NAME_RE = re.compile(r"^name:\s*['\"]?([^'\"\r\n]+?)['\"]?\s*$", re.MULTILINE)


def agent_names(directory):
    names = set()
    for path in glob.glob(os.path.join(directory, "*.md")):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                head = fh.read(2048)
        except OSError:
            continue
        match = NAME_RE.search(head) if head.startswith("---") else None
        names.add(match.group(1).strip() if match else os.path.splitext(os.path.basename(path))[0])
    return names


def configured(cwd):
    home = os.path.expanduser("~")
    names = agent_names(os.path.join(home, ".claude", "agents"))
    for root in {os.environ.get("CLAUDE_PROJECT_DIR") or "", cwd or ""}:
        if root:
            names |= agent_names(os.path.join(root, ".claude", "agents"))
    # Only INSTALLED plugins: the cache keeps uninstalled plugins' files, and their agents must not pass.
    plugin = set()
    try:
        with open(os.path.join(home, ".claude", "plugins", "installed_plugins.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        installed = (data.get("plugins") or data).keys()
    except (OSError, ValueError, AttributeError):
        installed = []
    for key in installed:
        name, _, market = key.partition("@")
        base = os.path.join(home, ".claude", "plugins", "cache", market or "*", name)
        for d in glob.glob(os.path.join(base, "**", "agents"), recursive=True):
            plugin |= agent_names(d)
    return names, plugin


def deny(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


# Old plans still name these; point them at the new name instead of a bare denial.
RENAMED = {'impl-light': 'impl-sonnet-low', 'impl-haiku': 'impl-sonnet-low', 'impl-standard': 'impl-sonnet-medium', 'impl-critical': 'impl-opus-medium', 'impl-high': 'impl-opus-high', 'impl-fable': 'impl-opus-medium', 'impl-fable-low': 'impl-opus-medium', 'impl-fable-medium': 'impl-opus-medium'}


def main():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Agent":
        return
    tool_input = payload.get("tool_input") or {}
    names, plugin = configured(payload.get("cwd"))
    listing = ", ".join(sorted(names)) or "(none found)"
    rule = " Rule: ~/.claude/rules/workflow.md 'Dispatching subagents'."

    if tool_input.get("model"):
        deny(
            "Agent dispatch blocked: do not pass `model`. The agent definition's frontmatter carries "
            "model + effort; pick the configured agent whose tier fits instead." + rule
        )

    kind = (tool_input.get("subagent_type") or "").strip()
    # Owner ruling 2026-10-17: a WRITING agent works in its own worktree so independent tasks run in
    # parallel and the session integrates one branch at a time. Read-only agents (review-*, audit,
    # planner, architect) and the orchestrator (which dispatches worktree agents itself) are exempt.
    if (kind.startswith("impl-") or kind.startswith("plugin:impl-")) and tool_input.get("isolation") != "worktree":
        deny(
            "Agent dispatch blocked: '%s' writes code, so dispatch it with isolation: \"worktree\" "
            "(owner ruling 2026-10-17: one worktree per independent task; the session merges). A fix "
            "small enough not to need one is done inline by the session, not by an agent." % kind + rule
        )
    ok = kind in names or (":" in kind and kind.split(":", 1)[1] in plugin)
    if not ok:
        shown = kind or "(omitted -> general-purpose)"
        if kind in RENAMED:
            deny(
                "Agent dispatch blocked: '%s' was renamed to '%s' (2026-09-30: names now state model and "
                "effort). Dispatch '%s'.%s" % (kind, RENAMED[kind], RENAMED[kind], rule)
            )
        deny(
            "Agent dispatch blocked: subagent_type '%s' is not a configured agent. Always dispatch a "
            "configured agent. Configured: %s.%s" % (shown, listing, rule)
        )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail open, but say so
        sys.stderr.write("agent-dispatch-guard: internal error, allowing dispatch: %r\n" % (exc,))
        sys.exit(0)
