"""Measure what the parallel-worktree workflow costs on this machine: disk per worktree and RAM per process.

Usage (Windows):  python tools/measure-footprint.py <workspace>
<workspace> is the directory holding your project checkouts and their .worktree/ folder.
"""
import os, subprocess, sys, glob, json

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 2:
    sys.exit(__doc__)
WS = sys.argv[1].replace("\\", "/").rstrip("/")


def is_reparse(p):
    try:
        return bool(os.lstat(p).st_file_attributes & 0x400) or os.path.islink(p)
    except OSError:
        return False


def du(path):
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not is_reparse(os.path.join(root, d))]
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def mb(n):
    return "%.0f MB" % (n / 1e6)


print("== worktrees on disk (junctions/symlinks NOT followed) ==")
rows = []
for wt in sorted(glob.glob(WS + "/.worktree/*/*")):
    if os.path.basename(wt) == ".meta" or not os.path.isdir(wt):
        continue
    proj = os.path.basename(os.path.dirname(wt))
    nm = os.path.join(wt, "node_modules")
    rows.append((proj, os.path.basename(wt), du(wt), is_reparse(nm)))
for proj, name, size, link in rows:
    print("  %-14s %-34s %8s  node_modules=%s" % (proj, name, mb(size), "junction" if link else "none/real"))
if rows:
    sizes = [r[2] for r in rows]
    print("  n=%d  mean=%s  min=%s  max=%s" % (len(rows), mb(sum(sizes) / len(sizes)), mb(min(sizes)), mb(max(sizes))))
for proj in sorted({r[0] for r in rows}):
    main = os.path.join(WS, proj)
    if os.path.isdir(main):
        print("  main checkout %-12s %8s  node_modules %s" % (proj, mb(du(main)), mb(du(os.path.join(main, "node_modules"))) if os.path.isdir(os.path.join(main, "node_modules")) else "n/a"))

print("\n== RAM per process (Windows working set) ==")
ps = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-Process | Where-Object { $_.ProcessName -match '^(claude|node|python|git|bash|powershell)$' } | "
    "Select-Object ProcessName, Id, WorkingSet64, @{n='Cmd';e={ (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine }} | ConvertTo-Json"],
    capture_output=True, text=True).stdout
procs = json.loads(ps) if ps.strip() else []
if isinstance(procs, dict):
    procs = [procs]
by = {}
for p in procs:
    cmd = (p.get("Cmd") or "")[:90]
    key = p["ProcessName"]
    if key == "node" and "claude" in cmd.lower():
        key = "node(claude)"
    by.setdefault(key, []).append(p["WorkingSet64"])
for k, v in sorted(by.items()):
    print("  %-14s n=%2d  total=%8s  mean=%8s  max=%8s" % (k, len(v), mb(sum(v)), mb(sum(v) / len(v)), mb(max(v))))
cl = by.get("claude", [])
if cl:
    print("  -> one Claude Code session ~ %s (mean of %d live)" % (mb(sum(cl) / len(cl)), len(cl)))

mem = subprocess.run(["powershell", "-NoProfile", "-Command",
    "$o=Get-CimInstance Win32_OperatingSystem; '{0:N0} MB total, {1:N0} MB free' -f ($o.TotalVisibleMemorySize/1KB), ($o.FreePhysicalMemory/1KB)"],
    capture_output=True, text=True).stdout.strip()
print("\n== machine ==\n  RAM:", mem)
disk = subprocess.run(["powershell", "-NoProfile", "-Command",
    "$d=Get-PSDrive C; '{0:N0} GB used, {1:N0} GB free' -f ($d.Used/1GB), ($d.Free/1GB)"], capture_output=True, text=True).stdout.strip()
print("  C: ", disk)
