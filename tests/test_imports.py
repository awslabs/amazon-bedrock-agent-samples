# Copyright 2024 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission

"""Regression tests for issues #146 and #104.

``src/utils/bedrock_agent.py`` used ``from typing import Self``. ``typing.Self`` was
only added in Python 3.11, but the setup docs (``src/README.md`` / ``src/utils/README.md``)
document a "Python 3.8 or later" floor, and AWS-native environments ship older interpreters
(CloudShell 3.9, SageMaker notebooks 3.10). The result was an immediate
``ImportError: cannot import name 'Self' from 'typing'`` on Python 3.8-3.10, before any
agent code could run.

These tests pin the fix: ``Self`` must be imported from ``typing_extensions`` (a 3.8+
backport) and annotation evaluation must be deferred via ``from __future__ import
annotations`` so the ``-> Self`` return annotation is never resolved at runtime.

The module performs live AWS calls at import time, so it cannot be imported wholesale
without credentials. These tests therefore exercise the import strategy itself, which is
exactly where issue #146's traceback stopped.
"""

import ast
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "src" / "utils" / "bedrock_agent.py"


def _from_imports(source):
    """Return the set of ``(module, imported_name)`` pairs for every ``from X import Y``."""
    pairs = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                pairs.add((node.module, alias.name))
    return pairs


def test_self_not_imported_from_stdlib_typing():
    """``Self`` must not come from stdlib ``typing`` (added only in 3.11) — issues #146/#104."""
    offenders = [(m, n) for m, n in _from_imports(MODULE.read_text()) if m == "typing" and n == "Self"]
    assert not offenders, (
        "`from typing import Self` only works on Python 3.11+, but this module documents a "
        "3.8+ floor. Import `Self` from `typing_extensions` instead."
    )


def test_future_annotations_enabled():
    """``from __future__ import annotations`` defers eval so ``-> Self`` is never resolved at runtime."""
    assert ("__future__", "annotations") in _from_imports(MODULE.read_text()), (
        "Add `from __future__ import annotations` so the `-> Self` annotation is never "
        "evaluated at runtime on any supported Python version."
    )


def test_self_imported_from_a_pre_311_safe_source():
    """``Self`` must come from a module that provides it on Python 3.8-3.10 (i.e. ``typing_extensions``).

    This is the import that issue #146's traceback died on. We assert the source is not stdlib
    ``typing`` and that it genuinely exposes ``Self`` on the running interpreter, without mutating
    ``typing`` internals (which would only exercise the test harness, not the module).
    """
    self_sources = {module for module, name in _from_imports(MODULE.read_text()) if name == "Self"}
    assert self_sources, "module does not import `Self` at all"
    assert "typing" not in self_sources, (
        "module imports `Self` from stdlib `typing`, which raises ImportError on Python 3.8-3.10"
    )
    for module in self_sources:
        imported = __import__(module, fromlist=["Self"])
        assert hasattr(imported, "Self"), f"`{module}` does not provide `Self`"
