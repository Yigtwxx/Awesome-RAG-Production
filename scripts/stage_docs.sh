#!/usr/bin/env bash
# Stage the repository's root markdown into ./docs for the mkdocs build.
# The canonical source files stay at the repo root (README.md remains the repo's
# primary file); ./docs is generated and gitignored. mkdocs treats README.md as
# the section index, so the home page and all relative links resolve unchanged.
set -euo pipefail

cd "$(dirname "$0")/.."

rm -rf docs
mkdir -p docs

# Files published on the site (REPO-ANALIZ.md is intentionally excluded — it is
# an internal audit). LICENSE is copied so the README's license link resolves.
PAGES=(
  README.md
  FAQ.md
  ROADMAP.md
  CHANGELOG.md
  CONTRIBUTING.md
  SECURITY.md
  CODE_OF_CONDUCT.md
  benchmarks.md
  rag-pitfalls.md
  datasets.md
  showcase.md
  books.md
  blogs.md
  LICENSE
)

for f in "${PAGES[@]}"; do
  if [ -f "$f" ]; then
    cp "$f" "docs/$f"
  else
    echo "stage_docs: warning — '$f' not found, skipping" >&2
  fi
done

echo "stage_docs: staged ${#PAGES[@]} files into ./docs"
