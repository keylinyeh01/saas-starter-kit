"""
Minimal Gherkin (BDD) runner with no external dependencies.

Scope:
- Support Feature / Scenario and step keywords: Given/When/Then/And/But
- Map steps to Python functions via regex patterns
- Fail fast with helpful errors
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Pattern, Tuple


StepFn = Callable[..., Any]


@dataclass(frozen=True)
class StepDef:
    pattern: Pattern[str]
    fn: StepFn


_STEP_DEFS: List[StepDef] = []


def step(pattern: str) -> Callable[[StepFn], StepFn]:
    """
    Register a step definition.

    Args:
        pattern: Regex pattern applied to the raw step line (without keyword).
    """

    compiled = re.compile(pattern)

    def _decorator(fn: StepFn) -> StepFn:
        _STEP_DEFS.append(StepDef(pattern=compiled, fn=fn))
        return fn

    return _decorator


@dataclass
class ParsedScenario:
    name: str
    steps: List[Tuple[str, str]]  # (keyword, text)


def parse_feature(feature_path: str | Path) -> List[ParsedScenario]:
    path = Path(feature_path)
    raw = path.read_text(encoding="utf-8")

    scenarios: List[ParsedScenario] = []
    current: ParsedScenario | None = None

    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower().startswith("feature:"):
            continue
        if s.lower().startswith("scenario:"):
            current = ParsedScenario(name=s.split(":", 1)[1].strip(), steps=[])
            scenarios.append(current)
            continue

        m = re.match(r"^(Given|When|Then|And|But)\s+(.*)$", s)
        if m and current is not None:
            current.steps.append((m.group(1), m.group(2)))

    return scenarios


def run_feature(feature_path: str | Path, context: Dict[str, Any] | None = None) -> None:
    ctx: Dict[str, Any] = context or {}
    scenarios = parse_feature(feature_path)
    if not scenarios:
        raise AssertionError(f"No scenarios found in feature: {feature_path}")

    for scenario in scenarios:
        for _kw, step_text in scenario.steps:
            _run_step(step_text, ctx)


def _run_step(step_text: str, ctx: Dict[str, Any]) -> None:
    for sd in _STEP_DEFS:
        m = sd.pattern.fullmatch(step_text)
        if m:
            sd.fn(ctx, *m.groups())
            return
    raise AssertionError(f"Undefined step: {step_text}")

