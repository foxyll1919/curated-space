"""The eval CLI.

This module is the only place that imports the backend. `curated_evals` imports
nothing from `app`, which keeps the metric code testable without FastAPI, a
database or the Gemini SDK, and keeps the backend from depending on the harness.

Two provider modes:

- **live** (default): the real `GeminiExtractor`, needs `GEMINI_API_KEY`.
- **fake**: a scripted provider with deterministic latency and token counts, so
  the harness, the report and the tests run anywhere with no key and no network.
  Reports it produces record `provider: "fake"`, so its numbers cannot be quoted
  as a measurement.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any


ML_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ML_DIR.parent / "backend"
DEFAULT_TAXONOMY = ML_DIR / "taxonomy" / "legacy-8.json"
DEFAULT_REPORT_DIR = ML_DIR / "evals" / "reports"


def _bootstrap() -> None:
    """Put the backend and `curated_ml` on `sys.path`.

    `curated_ml` is installed into the backend environment as an editable path
    dependency; adding the backend here is what lets this CLI benchmark the
    shipping firewall and extractor without either package importing the other.
    """
    for path in (BACKEND_DIR, ML_DIR / "src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


_bootstrap()

from curated_evals.config import (  # noqa: E402
    CANDIDATE_MODELS,
    DEFAULT_RESOLUTIONS,
    DEFAULT_THINKING,
    EvalConfig,
    by_name,
    matrix,
)
from curated_evals.dataset import LabeledSet, load_set, write_label_template  # noqa: E402
from curated_evals.fake import build_fake_extractor  # noqa: E402
from curated_evals.report import build_report, render_table, write_report  # noqa: E402
from curated_evals.runner import ItemRecord, run_config  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evals.run",
        description="Benchmark the Gemini extractor and the local classifier.",
    )
    parser.add_argument("--set", dest="set_path", help="folder with labels.csv, or a CSV")
    parser.add_argument("--config", help="one config name from --list-configs")
    parser.add_argument("--all", action="store_true", help="sweep the comparison matrix")
    parser.add_argument("--models", nargs="+", default=list(CANDIDATE_MODELS))
    parser.add_argument(
        "--resolutions",
        nargs="+",
        default=list(DEFAULT_RESOLUTIONS),
        choices=["LOW", "MEDIUM", "HIGH"],
    )
    parser.add_argument(
        "--thinking",
        nargs="+",
        default=list(DEFAULT_THINKING),
        choices=["minimal", "low", "medium", "high"],
    )
    parser.add_argument(
        "--provider-labels",
        action="store_true",
        help="also ask Gemini for a taxonomy enum label, to compare against the classifier",
    )
    parser.add_argument("--taxonomy", default=str(DEFAULT_TAXONOMY))
    parser.add_argument("--out", help="write the JSON report to this path")
    parser.add_argument("--out-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--label", help="report name; defaults to a timestamp")
    parser.add_argument("--limit", type=int, help="evaluate only the first N items")
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="run each item N times; 2 is how the cache is measured",
    )
    parser.add_argument(
        "--fake",
        action="store_true",
        help="scripted provider instead of Gemini (no key, no network)",
    )
    parser.add_argument("--list-configs", action="store_true", help="print the matrix and exit")
    parser.add_argument(
        "--init-labels", help="write an empty labels.csv for the images in this folder and exit"
    )
    parser.add_argument("--no-classifier", action="store_true")
    parser.add_argument("--notes", default="", help="free text recorded in the report")
    return parser


def select_configs(args: argparse.Namespace) -> list[EvalConfig]:
    if args.all:
        return list(
            matrix(
                models=tuple(args.models),
                resolutions=tuple(args.resolutions),
                thinking_levels=tuple(args.thinking),
                provider_labels=args.provider_labels,
                use_classifier=not args.no_classifier,
            )
        )
    return [by_name(matrix(provider_labels=args.provider_labels), args.config)]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.init_labels:
        path = write_label_template(args.init_labels, taxonomy_path=args.taxonomy)
        print(f"wrote {path}. Fill in the 'category' column by hand; the harness will not.")
        return 0

    try:
        configs = select_configs(args)
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2

    if args.list_configs:
        for config in configs:
            print(f"{config.name:<60} {config.model}")
        return 0

    if not args.set_path:
        print("error: --set is required (or use --init-labels / --list-configs)", file=sys.stderr)
        return 2

    set_ = load_set(args.set_path, args.taxonomy)
    if args.limit:
        set_ = LabeledSet(
            items=set_.items[: args.limit], taxonomy=set_.taxonomy, split=set_.split, root=set_.root
        )

    if not args.fake and not has_key():
        print(
            "error: GEMINI_API_KEY is not set. Use --fake to exercise the harness with no key, "
            "or set the key in backend/.env.",
            file=sys.stderr,
        )
        return 2

    runs = [_run_one(config, set_, args) for config in _with_progress(configs)]

    from app.core.pricing import load_pricing_table

    table = load_pricing_table()
    report = build_report(
        runs,
        set_,
        pricing={
            "verified_on": table.verified_on,
            "source": table.source,
            "tier": table.tier,
            "output_includes_thinking_tokens": table.output_includes_thinking_tokens,
            "provider": "fake" if args.fake else "live",
        },
        notes=args.notes,
    )
    print(render_table(report))

    out = args.out or _default_report_path(args, set_)
    write_report(report, out)
    print(f"\nreport: {out}", file=sys.stderr)
    return 0


def _with_progress(configs: list[EvalConfig]) -> list[EvalConfig]:
    return configs


class Prepared:
    """The two fields `run_config` reads off a prepared image."""

    def __init__(self, model_input: Any, content_sha256: str) -> None:
        self.model_input = model_input
        self.content_sha256 = content_sha256


def _run_one(config: EvalConfig, set_: LabeledSet, args: argparse.Namespace):
    from app.core.config import Settings
    from app.core.pricing import estimate_cost_usd
    from app.services.analysis_cache import cache_key
    from app.services.classification.sklearn_svc import SklearnSvcClassifier
    from app.services.extraction.base import CacheIdentity, ModelInput
    from app.services.extraction.gemini import GeminiExtractor
    from app.services.extraction.prompts import PROMPT_VERSION
    from app.services.image_firewall import sanitize_image
    from curated_ml.taxonomy import load_taxonomy

    settings = Settings().model_copy(update=config.provider_overrides())
    labels = load_taxonomy(args.taxonomy).labels

    def identity() -> CacheIdentity:
        # Keyed on the config, not on the extractor, so a sweep cannot serve one
        # cell's cached answer to another.
        return CacheIdentity(
            model=config.model,
            prompt_version=PROMPT_VERSION,
            schema_version=("metadata-v1+labels" if config.provider_labels else "metadata-v1"),
        )

    def prepare(data: bytes) -> Prepared:
        sanitized = sanitize_image(data, settings)
        return Prepared(
            model_input=ModelInput(data=sanitized.model_input_bytes, mime="image/png"),
            content_sha256=sanitized.content_sha256,
        )

    extractor = build_fake_extractor(config, labels) if args.fake else GeminiExtractor(settings)

    classifier = None
    if config.use_classifier:
        adapter = SklearnSvcClassifier(settings.classifier_artifact, strict_version=False)
        try:
            adapter.load()
            classifier = adapter
        except Exception as exc:  # noqa: BLE001 - one missing artifact must not hide the rest
            print(
                f"warning: classifier unavailable ({type(exc).__name__}); "
                "reporting the provider arm only",
                file=sys.stderr,
            )

    def progress(index: int, total: int, record: ItemRecord) -> None:
        status = "ok" if record.ok else f"FAIL {record.error_code}"
        print(
            f"   {index}/{total} {record.item_id} {status} {record.latency_ms}ms "
            f"in={record.prompt_tokens} out={record.output_tokens}",
            file=sys.stderr,
        )

    return run_config(
        config,
        set_,
        extractor=extractor,
        classifier=classifier,
        prepare=prepare,
        estimate_cost=lambda model, prompt, output: estimate_cost_usd(
            model, prompt_tokens=prompt, output_tokens=output
        ),
        cache=_InMemoryCache(),
        cache_key=lambda sha, _cfg: cache_key(sha, identity()),
        facet=set_.facet,
        repeats=args.repeats,
        on_progress=progress,
    )


class _InMemoryCache:
    """Cache double using the production key, so hit rate means what it says.

    The row re-validation the real cache does on read is mirrored here: a value
    that no longer satisfies the schema is a miss, not a corrupt result.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        from app.services.extraction.schema import ExtractedMetadata

        value = self._store.get(key)
        if value is None:
            return None
        try:
            return ExtractedMetadata.model_validate(value)
        except Exception:  # noqa: BLE001 - an unusable row is a miss
            return None

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value.model_dump(mode="json")


def _default_report_path(args: argparse.Namespace, set_: LabeledSet) -> Path:
    from curated_evals.dataset import SYNTHETIC_SPLIT

    name = args.label or (
        "synthetic" if set_.split == SYNTHETIC_SPLIT else f"eval-{dt.datetime.now():%Y%m%d-%H%M%S}"
    )
    return Path(args.out_dir) / f"{name}.json"


def has_key() -> bool:
    from app.core.config import Settings

    key = Settings().gemini_api_key
    return key is not None and bool(key.get_secret_value().strip())


if __name__ == "__main__":
    raise SystemExit(main())
