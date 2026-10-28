# Do not over-engineer — coding, implementing or suggesting (user ruling 2026-10-10)

- **Build the smallest thing that meets the request.** No abstraction, config option, helper,
  layer, fallback or "future-proofing" the task did not ask for. Three similar lines beat a
  premature abstraction. Extend existing code before adding a file, module or agent.
- **Never suggest a new stack** — library, framework, service, tool, database, build step or
  agent type — **without a meaningful purpose**: name the concrete problem it solves here that
  the current stack cannot, and what it costs. No purpose, no suggestion.
- **Suggestions stay proportional**: the one fix that matters, not a menu of improvements.
  Reviewers flag real defects, not missing sophistication.

# Web research — WebSearch to FIND the page, curl to READ it. Never WebFetch.

**Research on the internet is MANDATORY on every task that rests on a real-world fact, in every
project and every session (user ruling 2026-10-27). It is a SECOND OPINION: it adds information and
references beside the local sources (the code, the docs, the user's words); it never replaces reading
them, and a fact recalled from training data is not a reference.** The split is by job, not by
preference:

| Job | Tool |
|---|---|
| **Discovery** — which URL is current | **`WebSearch`** (allowed; curl cannot search) |
| **Retrieval** — read that URL | **`curl` via Bash** (`WebFetch` is denied) |

`curl` wins retrieval outright: raw bytes, real HTTP status and headers, and **binary** files
(GeoTIFF, PDF, zip) that `WebFetch` cannot handle at all.

## The research store — `docs/research/` in every project (user ruling 2026-10-27)

**A fetched page is recorded once and read many times.** Every project keeps `docs/research/`, one
file per topic, each a source table: URL · fetched date · HTTP status · quoted line(s) · used for ·
verdict (SAYS IT / PARTLY / DOES NOT SAY IT / DEAD / PAYWALLED / UNVERIFIED). Its `README.md` is the
contract (template: the `docs/research/README.md` of a project that already has one; copy it into a
project that lacks one).

- **Before fetching: `grep -rn "<domain or phrase>" docs/research/`.** A hit is read, not re-fetched,
  unless it is older than the fact's shelf life (tariff: a quarter; factor: a year; standard or
  datasheet: a version change) or marked UNVERIFIED.
- **After fetching: add the row in the same session**, in the topic file, dead links included with
  the replacement found. A fetch that leaves no row was wasted.
- The store also carries the references found **beside** the ones a registry or doc already cites,
  so the next reader can widen the search instead of repeating it.
- Subagent briefs name the store: "check `docs/research/` first; append your source log there as
  rows" — a research agent that returns only a transcript leaves nothing behind.

## Subagents — paste this into every dispatch prompt

A subagent does **not** reliably inherit this rule, and it will reach for `WebFetch` by default. **Every
`Agent` dispatch whose task could involve looking anything up must carry this block verbatim** — it is
cheap, and a research agent that quietly answered from memory is worse than no agent:

> **Research method — mandatory.** Use **`WebSearch`** only to *find* the right URL. Use **`curl` via
> the Bash tool** to *read* it — `WebFetch` is denied and must not be attempted. Verify against
> primary sources, never from memory; if a fact cannot be verified, report it as **UNVERIFIED**
> rather than filling the gap. Most vendor docs are JS-heavy, so fetch then strip tags (write the
> helper to a file on Windows — inline heredocs and `-c` regexes get mangled by shell quoting; print
> non-ASCII with `sys.stdout.reconfigure(encoding='utf-8')`, since `python -I` ignores `PYTHONIOENCODING`). Prefer structured endpoints where they exist:
> `api.github.com`, `registry.npmjs.org`, `data.jsdelivr.com`, `pypi.org/pypi/<pkg>/json`. Never echo
> a secret — read keys into a shell variable, never print the value. **Before fetching, `grep -rn`
> the project's `docs/research/` for the page and read the recorded row instead; after fetching,
> append a row (URL · date · HTTP · quoted line · used for · verdict) to `docs/research/<topic>.md`.**

## Why

Training data goes stale and reads as confident. Prices, API field names, ToS clauses and library
versions are exactly the facts that change and exactly the facts that get quoted as authority.

**Guessing a URL from memory is still answering from training data.** A guess that 404s is harmless —
you find out. **A guess that resolves to a stale page is a silent failure.** Real case: `developer.nrel.gov`
died in 2026-05 and moved to `developer.nlr.gov`; curling the remembered host would have returned
something, and it would have been wrong. **Search for the current location before curling a URL you
are recalling rather than one you were given.**

## Working recipes

Most vendor docs are JS-heavy; fetch, then strip tags:

```bash
curl -sL --max-time 30 -A "Mozilla/5.0" "<url>" -o /tmp/p.html
python -c "
import re,html
s=open(r'/tmp/p.html',encoding='utf-8',errors='ignore').read()
s=re.sub(r'(?s)<(script|style|head)[^>]*>.*?</\1>',' ',s)
s=re.sub(r'(?s)<[^>]+>',' ',s); s=html.unescape(s); s=re.sub(r'[ \t]+',' ',s)
print('\n'.join(l.strip() for l in s.split('\n') if l.strip()))
"
```

- On Windows, write the helper to a **file** and run it — heredocs and inline `-c` regexes get mangled
  by shell quoting. Print non-ASCII with `sys.stdout.reconfigure(encoding='utf-8')`: `python -I`
  (required on downloaded files) ignores `PYTHONIOENCODING`.
- Structured sources beat scraping: `api.github.com`, `registry.npmjs.org`, `data.jsdelivr.com`,
  `pypi.org/pypi/<pkg>/json`.
- **Never echo a secret.** Read keys into a shell variable from `.env`; never print the value.

## Reporting

State what you fetched and when. If a fact could not be verified, say **UNVERIFIED** — never fill the
gap from memory and present it as checked.
