# Design: AgentHarness documentation site + cookbook

**Date:** 2026-06-25
**Status:** Approved-in-principle (brainstormed with the user; tooling + sync rigor chosen)
**Owner:** Claude plans/verifies, Codex implements (see `CLAUDE.md`).

## Goal

Make AgentHarness adoptable. A developer **or an agent** landing cold should "get it" in
five minutes and find a runnable recipe for their exact case. Docs are make-or-break for
adoption and are the next roadmap item after the public repo + green CI.

Success criteria:

- A first-time reader understands the thesis and runs a working example (no API key) in
  under 5 minutes.
- Every code snippet in the docs is **executed in CI** — docs provably cannot drift.
- The API reference is generated from the real docstrings (always current).
- An agent can consume the whole corpus via `llms.txt` / `llms-full.txt`.
- The site builds and deploys to GitHub Pages automatically on push to `main`.

## Decisions (locked)

| Decision | Choice | Why |
|---|---|---|
| Tooling | **mkdocs-material** | Python-native, plain Markdown in-repo, free, zero SaaS lock-in; the Python-community standard (FastAPI, Pydantic, Textual). Matches the project's zero-dependency/longevity ethos. |
| API reference | **mkdocstrings[python]** | Renders the API straight from real docstrings — can't drift from signatures. |
| Snippet integrity | **Executable, tested docs** | Every fenced snippet runs in CI (`markdown-exec` for rendering + a `pytest`-driven extraction check) and `mkdocs build --strict` fails on broken links/refs. On-thesis: a trust-focused library proves its own docs. |
| Hosting | **GitHub Pages** via CI | Free, in-repo, no external service. |
| Out of scope (YAGNI) | versioned docs (mike), i18n, blog, custom domain | Add when there is an audience. |

## Information architecture

```
Home                  pitch + 12-line quickstart; the "why" in 30 seconds
Getting started/
  Install             pip install, the [anthropic] extra
  Your first run      FakeModel -> run -> inspect events (no API key)
  Record & replay     save a trace, replay byte-identical, DivergenceError
Core concepts/
  The thesis          decide / perform / reduce; why purity buys the 4 properties
  State & events      the data algebra, JSON round-trip
  Effects & the runner the only impure part; how effects are recorded
  Determinism kit     Trace, replay, divergence
Cookbook/             task-oriented runnable recipes (see list)
Providers/
  Anthropic           a real recorded model call; OpenAI/Ollama marked "planned"
Guides/
  Testing agents      FakeModel, assert_used_tool / assert_answer, pytest
  Tools with @tool    JSON schema from type hints
Reference/            mkdocstrings API for core, agentharness, contrib
llms.txt, llms-full.txt   at site root for agent consumption
```

Navigation is configured explicitly in `mkdocs.yml` (no auto-nav) so ordering tells a
story: pitch -> first success -> mental model -> "recipe for my case" -> depth.

## Cookbook recipes (initial set)

Each recipe is a single Markdown page: a one-line "when you want to…", a runnable snippet
(executed in CI), and a short "why it works". Ordered by how commonly a newcomer needs them.

1. **Unit-test an agent with zero network** — `FakeModel` + `assert_used_tool`/`assert_answer`.
2. **Record a real run and replay it offline** — `.trace.save()` then `replay()`.
3. **Catch a regression** — replay a saved trace against changed code; read `DivergenceError`.
4. **Define a tool with `@tool`** — schema generated from type hints; tool stays callable.
5. **A multi-step tool-use loop** — model calls a tool, sees the result, answers.
6. **Inspect / stream the event log** — iterate `Run` for a typed event stream.
7. **Swap providers without changing agent code** — same `Agent`, different `Model`.
8. **Run async** — `arun` / `astream`.
9. **Persist & diff traces** — observability for free; traces are plain JSONL.
10. **Bring your own model** — implement the `Model` protocol (`respond`).

## Docs <-> code synchronization

- **Snippets execute in CI.** A new `docs` CI job runs the snippets and `mkdocs build
  --strict`. Mechanism: `markdown-exec` renders/executes fenced ```python exec="on"```
  blocks at build time, so `mkdocs build --strict` failing on a raised exception is the
  test. (Equivalent fallback if markdown-exec proves awkward: a small pytest that extracts
  ```python``` blocks tagged for execution and `exec`s them.) Pick markdown-exec first.
- **Examples are referenced, not duplicated.** The existing `examples/quickstart.py` and
  `examples/agent_quickstart.py` remain CI smoke tests; docs link to them and may inline
  excerpts via snippet includes (`pymdownx.snippets`) rather than copy-paste.
- **API reference from docstrings** via mkdocstrings — signatures and types always current.
- **No API key in CI.** All executed snippets use `FakeModel`; the Anthropic page shows a
  real call but is **not** executed in CI (marked non-exec), shown as illustration.

## Build, CI, and deploy

- A new docs dependency group (`docs`) in the workspace `pyproject.toml`:
  `mkdocs-material`, `mkdocstrings[python]`, `markdown-exec`, `pymdown-extensions`.
  Kept out of the library runtime deps (core stays zero-dependency).
- `mkdocs.yml` at repo root: material theme, navigation, `pymdownx` extensions
  (superfences, snippets, tabbed, admonition), mkdocstrings + markdown-exec plugins,
  social/repo links, search.
- **CI:** add a `docs` job to `ci.yml` — `uv sync --group docs` then `mkdocs build
  --strict` (this both checks links and executes snippets). Runs on PRs and `main`.
- **Deploy:** a separate `docs-deploy.yml` workflow on push to `main` that builds and
  publishes to GitHub Pages (`actions/deploy-pages`), with `pages: write` + `id-token:
  write` permissions and a `github-pages` environment. Keep deploy separate from the
  required CI gate so a Pages hiccup never blocks merges.
- **`llms.txt`:** authored `docs/llms.txt` (curated links + one-liners). `llms-full.txt`
  generated at build time by concatenating the Markdown sources (a tiny `mkdocs` hook or a
  `scripts/build_llms_full.py` invoked in the docs job and copied into `site/`).

## Risks / notes

- markdown-exec executing at build time means a flaky snippet fails the build — that is the
  point, but keep snippets deterministic (always `FakeModel`, fixed inputs).
- mkdocstrings needs the packages importable in the docs env — `uv sync --group docs` must
  include the three workspace packages (already dev deps).
- GitHub Pages must be enabled once in repo settings (source: GitHub Actions). One-time
  manual step; note it in `HANDOFF.md`.

## Definition of done

- `uv run mkdocs build --strict` is clean locally and in CI; all snippets execute.
- Site deploys to `https://aafre.github.io/agentharness/` (or the configured Pages URL).
- All ten cookbook recipes present and executing.
- `llms.txt` + `llms-full.txt` served at the site root.
- README links to the docs site; `HANDOFF.md` updated.
