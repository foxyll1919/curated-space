"""Run one eval config over a set and collect the numbers.

The runner deliberately drives the same firewall -> extractor -> classifier path
that serving uses, rather than a reimplementation, so a benchmark result is a
statement about the shipping code and not about a benchmark-only copy of it.

Two things it will not do:

- It will not invent a label. An item with no gold label still runs (that is how
  latency and cost get measured on a freshly-dropped folder) but it contributes
  nothing to accuracy.
- It will not price an unknown model at zero. `estimate_cost` returning None is
  carried through to the report as `null`.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from curated_ml.text import build_text

from curated_evals.config import EvalConfig
from curated_evals.dataset import EvalItem, LabeledSet
from curated_evals.metrics import (
    LabelMetrics,
    LabelObservation,
    agreement,
    score_items,
    score_latency,
    summarize_to_dict,
)


class PreparedInput(Protocol):
    """What the firewall hands to the extractor. Duck-typed on purpose.

    `model_input` is already the backend's `ModelInput`, so this module never
    imports the backend and the benchmark cannot drift from serving by way of a
    differently-shaped payload.
    """

    model_input: Any
    content_sha256: str


class RunCache(Protocol):
    """The subset of the analysis cache the harness needs to measure hit rate.

    The production implementation is keyed by
    `sha256(pixels) | model | prompt_version | schema_version`; the harness
    supplies one with the same key so "did the cache save a call" is answered by
    the real key logic rather than by a set of filenames.
    """

    def get(self, key: str) -> Any | None: ...

    def put(self, key: str, value: Any) -> None: ...


@dataclass(frozen=True)
class ItemRecord:
    """One item's outcome. Carries ids, counts and labels, never the metadata.

    Titles, descriptions and tags are deliberately absent: a report is a file
    that gets read and shared, and screenshot content does not belong in one.
    `--include-samples` writes them to a separate file for error review.
    """

    item_id: str
    ok: bool
    error_code: str | None = None
    latency_ms: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    est_cost_usd: float | None = None
    provider_label: str | None = None
    classifier_label: str | None = None
    classifier_abstained: bool | None = None
    classifier_score: float | None = None
    cache_hit: bool = False


@dataclass(frozen=True)
class RunResult:
    config: EvalConfig
    records: tuple[ItemRecord, ...]
    classifier_metrics: LabelMetrics | None = None
    provider_metrics: LabelMetrics | None = None
    agreement_rate: float | None = None
    agreement_n: int = 0
    latency: dict[str, int | None] = field(default_factory=dict)
    cost: dict[str, float | None] = field(default_factory=dict)
    provider_calls: int = 0
    cache_hits: int = 0
    failures: tuple[str, ...] = ()

    @property
    def items(self) -> int:
        return len(self.records)

    @property
    def cache_hit_rate(self) -> float:
        total = self.provider_calls + self.cache_hits
        return self.cache_hits / total if total else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.as_dict(),
            "items": self.items,
            "provider_calls": self.provider_calls,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "failures": list(self.failures),
            "classifier": summarize_to_dict(self.classifier_metrics)
            if self.classifier_metrics
            else None,
            "provider_labels": summarize_to_dict(self.provider_metrics)
            if self.provider_metrics
            else None,
            "agreement": {
                "rate": self.agreement_rate,
                "n": self.agreement_n,
            },
            "latency": self.latency,
            "cost": self.cost,
            "records": [
                {
                    "item_id": r.item_id,
                    "ok": r.ok,
                    "error_code": r.error_code,
                    "latency_ms": r.latency_ms,
                    "prompt_tokens": r.prompt_tokens,
                    "output_tokens": r.output_tokens,
                    "thinking_tokens": r.thinking_tokens,
                    "est_cost_usd": r.est_cost_usd,
                    "provider_label": r.provider_label,
                    "classifier_label": r.classifier_label,
                    "classifier_abstained": r.classifier_abstained,
                    "classifier_score": r.classifier_score,
                    "cache_hit": r.cache_hit,
                }
                for r in self.records
            ],
        }


def run_config(
    config: EvalConfig,
    set_: LabeledSet,
    *,
    extractor: Any,
    classifier: Any | None = None,
    prepare: Callable[[bytes], PreparedInput],
    estimate_cost: Callable[[str, int, int], float | None],
    cache: RunCache | None = None,
    cache_key: Callable[[str, EvalConfig], str] | None = None,
    facet: str | None = None,
    repeats: int = 1,
    on_progress: Callable[[int, int, ItemRecord], None] | None = None,
) -> RunResult:
    """Run `config` over every item in `set_`, `repeats` times each.

    `repeats > 1` exists to measure the cache honestly: the second pass over the
    same pixels must cost nothing. The default of 1 means every item makes a real
    provider call, which is what you want when comparing models.
    """
    records: list[ItemRecord] = []
    plan: list[EvalItem] = list(set_.items) * max(1, repeats)
    total = len(plan)
    facet_name = facet or set_.facet

    for index, item in enumerate(plan, start=1):
        record = _run_item(
            item,
            config=config,
            extractor=extractor,
            classifier=classifier if config.use_classifier else None,
            prepare=prepare,
            estimate_cost=estimate_cost,
            cache=cache,
            cache_key=cache_key,
            facet=facet_name,
        )
        records.append(record)
        if on_progress is not None:
            on_progress(index, total, record)

    return _summarize(config, set_, records, facet=facet_name)


def _run_item(
    item: EvalItem,
    *,
    config: EvalConfig,
    extractor: Any,
    classifier: Any | None,
    prepare: Callable[[bytes], PreparedInput],
    estimate_cost: Callable[[str, int, int], float | None],
    cache: RunCache | None,
    cache_key: Callable[[str, EvalConfig], str] | None,
    facet: str,
) -> ItemRecord:
    prepared = prepare(item.path.read_bytes())
    key = cache_key(prepared.content_sha256, config) if cache_key else None

    if cache is not None and key is not None:
        cached = cache.get(key)
        if cached is not None:
            # A hit costs zero calls and zero tokens; latency is the lookup.
            return ItemRecord(
                item_id=item.id,
                ok=True,
                latency_ms=0,
                cache_hit=True,
                classifier_label=None,
            )

    started = time.perf_counter()
    try:
        result = extractor.extract(prepared.model_input)
    except Exception as exc:  # noqa: BLE001 - a failure is a data point, not a crash
        return ItemRecord(
            item_id=item.id,
            ok=False,
            error_code=_error_code(exc),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    latency_ms = int((time.perf_counter() - started) * 1000)

    usage = result.usage
    cost = estimate_cost(
        result.model, usage.prompt_tokens, usage.output_tokens + usage.thinking_tokens
    )

    classifier_label: str | None = None
    classifier_abstained: bool | None = None
    classifier_score: float | None = None
    if classifier is not None:
        try:
            prediction = classifier.predict(
                build_text(result.metadata.title, result.metadata.description, result.metadata.tags)
            )
            label = prediction.labels.get(facet)
            if label is None and prediction.labels:
                # The adapter keys by whatever facet the taxonomy declares. Fall
                # back to its single value rather than dropping the observation.
                label = next(iter(prediction.labels.values()))
            classifier_label = label
            classifier_abstained = prediction.abstained
            classifier_score = prediction.score
        except Exception:  # noqa: BLE001 - the classifier is a challenger
            classifier_abstained = None

    if cache is not None and key is not None:
        cache.put(key, result.metadata)

    return ItemRecord(
        item_id=item.id,
        ok=True,
        latency_ms=latency_ms,
        prompt_tokens=usage.prompt_tokens,
        output_tokens=usage.output_tokens,
        thinking_tokens=usage.thinking_tokens,
        est_cost_usd=cost,
        provider_label=getattr(result, "label", None),
        classifier_label=classifier_label,
        classifier_abstained=classifier_abstained,
        classifier_score=classifier_score,
    )


def _error_code(exc: Exception) -> str:
    return getattr(exc, "code", None) or type(exc).__name__


def _summarize(
    config: EvalConfig, set_: LabeledSet, records: Sequence[ItemRecord], *, facet: str
) -> RunResult:
    gold = {item.id: item.gold_label for item in set_.items}

    ok_records = [r for r in records if r.ok and not r.cache_hit]

    classifier_observations = [
        LabelObservation(
            item_id=r.item_id,
            gold=gold.get(r.item_id),
            predicted=r.classifier_label,
            abstained=bool(r.classifier_abstained),
        )
        for r in records
        if r.classifier_abstained is not None
    ]
    classifier_metrics = score_items(classifier_observations) if classifier_observations else None

    provider_observations = [
        LabelObservation(
            item_id=r.item_id,
            gold=gold.get(r.item_id),
            predicted=r.provider_label,
            abstained=False,
        )
        for r in records
        if r.provider_label is not None
    ]
    provider_metrics = score_items(provider_observations) if provider_observations else None

    agreements = [
        value
        for r in records
        if (value := agreement(r.provider_label, r.classifier_label)) is not None
    ]

    latencies = [r.latency_ms for r in ok_records]
    latency = score_latency(latencies)
    n = len(ok_records)
    total_cost = sum(r.est_cost_usd for r in ok_records if r.est_cost_usd is not None)
    all_priced = all(r.est_cost_usd is not None for r in ok_records) if ok_records else True

    cost = {
        "usd_per_item": (total_cost / n) if (n and all_priced) else None,
        "total_usd": total_cost if all_priced else None,
        "prompt_tokens_per_item": (sum(r.prompt_tokens for r in ok_records) / n) if n else None,
        "output_tokens_per_item": (sum(r.output_tokens for r in ok_records) / n) if n else None,
        "thinking_tokens_per_item": (sum(r.thinking_tokens for r in ok_records) / n) if n else None,
        "priced": all_priced,
    }

    failures = tuple(f"{r.item_id}:{r.error_code}" for r in records if not r.ok)

    return RunResult(
        config=config,
        records=tuple(records),
        classifier_metrics=classifier_metrics,
        provider_metrics=provider_metrics,
        agreement_rate=(sum(agreements) / len(agreements)) if agreements else None,
        agreement_n=len(agreements),
        latency={
            "p50_ms": latency.p50_ms,
            "p95_ms": latency.p95_ms,
            "mean_ms": latency.mean_ms,
        },
        cost=cost,
        provider_calls=len(ok_records),
        cache_hits=sum(1 for r in records if r.cache_hit),
        failures=failures,
    )
