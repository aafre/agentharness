# Codex task: build the AgentHarness docs site + cookbook

**Role:** You (Codex) implement; Claude planned this and will verify with the green gate.
**Spec:** `docs/superpowers/specs/2026-06-25-docs-site-design.md` (read it first — it is the
source of truth; this file is the step-by-step build order).

## Ground rules (non-negotiable)

1. **`agentharness-core` keeps ZERO third-party runtime deps.** All docs tooling goes in a
   new `docs` dependency group in the **root** `pyproject.toml`, never in any package's deps.
2. **Every executed snippet uses `FakeModel`** — no network, no API keys. The Anthropic page
   shows a real call as illustration only and must NOT execute in CI.
3. **Docs must build clean under `--strict`.** Broken links, bad refs, or a snippet that
   raises = build failure. That is intended.
4. Work from the repo root (uv workspace). Do not touch library source under
   `packages/*/src` except to improve docstrings if one is missing/wrong (minimal, additive).
5. Match existing style. Plain Markdown. Keep prose tight (this is a trust-focused library).

## The green gate (must pass before you hand back)

```bash
uv sync --group docs
uv run ruff check && uv run mypy && uv run pytest -q   # existing gate still green
uv run mkdocs build --strict                            # new: builds + executes snippets
```

All must pass. If `markdown-exec` execution proves awkward for a given snippet, fall back to
the pytest-extraction approach described in the spec — but prefer markdown-exec.

## Build order

### 1. Dependencies + config
- Add a `docs` group to root `pyproject.toml` `[dependency-groups]`:
  `mkdocs-material`, `mkdocstrings[python]`, `markdown-exec`, `pymdown-extensions`.
- Create `mkdocs.yml` at repo root:
  - `site_name: AgentHarness`, `site_url`, `repo_url: https://github.com/aafre/agentharness`,
    `repo_name: aafre/agentharness`.
  - theme `material` with: navigation.tabs, navigation.sections, navigation.instant,
    content.code.copy, content.code.annotate, search.suggest; light/dark palette toggle.
  - markdown_extensions: `admonition`, `pymdownx.superfences`, `pymdownx.tabbed`
    (alternate_style), `pymdownx.snippets`, `pymdownx.highlight`, `toc` (permalink).
  - plugins: `search`, `markdown-exec`, `mkdocstrings` (python handler; show source,
    show signature with type annotations).
  - Explicit `nav:` exactly matching the IA in the spec (do NOT auto-generate nav).

### 2. Pages (create under `docs/`; this is the mkdocs docs_dir — set `docs_dir: docs`)
> NOTE: the repo already uses `docs/` for specs. Set `docs_dir: docs` and EXCLUDE
> `docs/superpowers/**` and `docs/codex-task-*.md` from the build via `exclude_docs` (or an
> mkdocs exclude plugin / `not_in_nav`). Do not move the existing specs.

Create these Markdown files (paths relative to `docs/`):
- `index.md` — the pitch (reuse README framing), the 30-second "why", a 12-line quickstart
  (executed: FakeModel -> run -> print result). Link to Getting started.
- `getting-started/install.md` — `pip install agentharness-core` (note: not yet on PyPI —
  show `pip install` and also "from source" via uv until published); the `[anthropic]` extra.
- `getting-started/first-run.md` — FakeModel, `State.start`, `run`, iterate events, print
  result. Executed snippet.
- `getting-started/record-replay.md` — `.trace.save`, `replay`, assert identical; show
  `DivergenceError` conceptually. Executed.
- `concepts/thesis.md` — decide/perform/reduce, the 4 properties table (from README), why
  purity. Prose + one small executed snippet showing a pure `reduce` call if natural.
- `concepts/state-and-events.md` — the data algebra; `to_dict`/`from_dict` round-trip
  (executed). 
- `concepts/effects-and-runner.md` — the only impure part; what gets recorded.
- `concepts/determinism-kit.md` — Trace/replay/divergence in depth.
- `cookbook/index.md` — index of the 10 recipes with one-line summaries + links.
- `cookbook/*.md` — one page per recipe (10 total) per the spec list, each with an executed
  `FakeModel` snippet (except where a recipe is about BYO model / providers — still no network).
- `providers/anthropic.md` — real `AnthropicModel` usage; snippet marked NON-executing.
- `guides/testing-agents.md` — FakeModel + assertion helpers + a pytest example (executed).
- `guides/tools.md` — `@tool` schema-from-type-hints (executed).
- `reference/core.md`, `reference/agentharness.md`, `reference/contrib.md` — mkdocstrings
  `::: agentharness_core` etc. (one identifier block per module surface).

Use `pymdownx.snippets` to include excerpts from `examples/quickstart.py` /
`examples/agent_quickstart.py` rather than duplicating them where natural.

### 3. llms.txt
- Author `docs/llms.txt` — the llms.txt format: H1 title, a blockquote summary, then
  sectioned lists of `[Page title](url): one-line description` for every doc page.
- Generate `llms-full.txt` at build time: add `scripts/build_llms_full.py` that concatenates
  the Markdown sources in nav order into `site/llms-full.txt`, and wire it via a simple
  mkdocs hook (`hooks:` in mkdocs.yml) or run it in the docs CI job after build. Ensure both
  files land at the site root and are reachable.

### 4. CI + deploy
- Edit `.github/workflows/ci.yml`: add a `docs` job (ubuntu, after quality/test or parallel)
  that runs `uv sync --group docs` then `uv run mkdocs build --strict`.
- Create `.github/workflows/docs-deploy.yml`: on push to `main`, build the site and deploy to
  GitHub Pages using `actions/configure-pages`, `actions/upload-pages-artifact`,
  `actions/deploy-pages`; permissions `pages: write`, `id-token: write`; environment
  `github-pages`. Keep it separate from the CI gate.

### 5. Wire-up + docs of record
- Add a docs badge + "Documentation" link to `README.md` pointing at the Pages URL.
- Update `HANDOFF.md`: docs site shipped; note the one-time manual step (enable GitHub Pages
  with source = GitHub Actions in repo settings).

## What to hand back

A summary of: files added/changed, the exact green-gate command output (all green), the
local `mkdocs build --strict` result, and any snippet you had to adjust to keep it
deterministic. Do NOT deploy or publish anything; Claude verifies and the user enables Pages.
