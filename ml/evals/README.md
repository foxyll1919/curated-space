# Eval harness

`python -m evals.run --set <csv-or-folder> --config <name>`

Milestone 6 exists so the provider choices are measurements rather than
defaults copied from the brief. It runs the **real** firewall, extractor and
classifier, so a result is a statement about the shipping code.

## Running it

All commands run from `ml/` in the backend environment, because the harness
benchmarks backend code and there is no key requirement for `--fake`:

```powershell
# Check the harness end to end with no key and no network.
uv run --project ..\backend python -m evals.run `
  --set evals\sets\synthetic --taxonomy taxonomy\legacy-8.json `
  --config "gemini-3.5-flash-lite|medium|minimal" --fake --provider-labels

# The real thing. Needs GEMINI_API_KEY in backend\.env.
uv run --project ..\backend python -m evals.run `
  --set ..\backend\tests\fixtures --taxonomy taxonomy\legacy-8.json `
  --all --models gemini-3.5-flash-lite gemini-3.1-flash-lite --provider-labels
```

Useful flags: `--all` sweeps the matrix, `--limit N` evaluates the first N items,
`--repeats 2` measures the cache (the second pass must make zero provider calls),
`--list-configs` prints the grid, and `--out`/`--out-dir` choose where the JSON
report lands.

## Labeling a set

The harness will not invent a label. To start labeling a folder of screenshots:

```powershell
uv run --project ..\backend python -m evals.run --init-labels "<folder>"
```

That writes `labels.csv` with the filenames listed and **every gold column
blank**. Fill in `category` by hand, using one of the labels in the taxonomy
file. Until you do, the report prints `n/a` for accuracy rather than a number
over an empty denominator.

## What the report contains

Per config: per-facet accuracy and macro-F1 against gold, per-class
precision/recall, abstain rate, p50/p95 latency, tokens per item, estimated
dollars per item, cache hit rate, provider enum labels (with `--provider-labels`),
Gemini-vs-classifier agreement, and every failure with its error code.

Rules the code enforces:

- **Accuracy is `n/a` without gold labels.** No denominator, no number.
- **An unpriced model costs `null`, not `$0.00`.** A model missing from
  `backend/app/core/gemini_pricing.json` has unknown cost, and a fake zero would
  pass the "< $0.002 per item" target while measuring nothing.
- **An abstention scores as a miss.** The classifier abstaining on 60% of items
  must not look better than one that guesses.
- **Reports never contain titles, descriptions or tags.** Screenshot content does
  not belong in a file that gets shared.
- **A generated set is labelled `split: "synthetic"`** in every report, and the
  table prints a warning. The set under `sets/synthetic/` is drawn by
  `curated_evals.synthetic`, not photographed.

## The synthetic set

`curated_evals.synthetic.build_synthetic_set` renders small mock screens, one
per taxonomy label. It exists so CI has something to run against. It measures
this code, never model quality.

## Layout

| Module | Responsibility |
|---|---|
| `config.py` | The comparison matrix as data. No code edit to sweep it. |
| `dataset.py` | Loading a labeled set, and refusing a broken one. |
| `metrics.py` | Accuracy, macro-F1, abstention, latency percentiles. |
| `runner.py` | Drives firewall -> extractor -> classifier, collects records. |
| `fake.py` | Scripted provider for CI. Deterministic, obviously fake. |
| `report.py` | JSON document and the printed table. |
| `synthetic.py` | The generated fixture set. |

`curated_evals` imports nothing from `app`. `ml/evals/run.py` is the only module
that knows the backend exists, which is what keeps the metrics testable without
FastAPI, a database or the Gemini SDK.