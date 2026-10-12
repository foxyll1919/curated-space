# Synthetic eval set

**These images are generated, not screenshots.** They exist so the harness, the
metric code and CI have something to run against without an API key.

Anything measured on this set says something about the code, never about model
quality. Every report built from this folder records `split: "synthetic"`.

Drop real screenshots in their own folder with a `labels.csv` and point
`python -m evals.run --set <folder>` at that instead.
