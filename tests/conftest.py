"""Shared fixtures for validator tests. Mutations start from the example design."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Callable

import pytest

from hangar.checks import validate
from hangar.design import Design, Scorecard, load_design

from testutil import EXAMPLE_PATH, statuses  # noqa: F401  (re-exported; helpers live in testutil)


@pytest.fixture
def example() -> Path:
    return EXAMPLE_PATH


@pytest.fixture
def mutate(example: Path) -> Callable[[Callable[[dict], None]], Scorecard]:
    def _mutate(fn: Callable[[dict], None]) -> Scorecard:
        base = load_design(example)
        data = copy.deepcopy(base.data)
        fn(data)
        design = Design(data=data, path=example)
        return validate(design)

    return _mutate
