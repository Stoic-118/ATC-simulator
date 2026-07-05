"""Architectural boundary guard: src/atc_sim/sim/ must stay headless.

Enforces CORE-03's "sim core never imports pygame" rule. This test scans
every .py file under src/atc_sim/sim/ for a top-level pygame import
statement and fails if one is found. It is implemented as a pure-Python
text scan (no shelling out to grep) so it runs identically on any platform.

src/atc_sim/app.py legitimately imports pygame but lives outside sim/, so
it is never in scope for this scan.
"""

from __future__ import annotations

import re
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent / "src" / "atc_sim" / "sim"

# Phase 2: navdata/ is sim-core reference data (usable by future separation
# math) and is guarded headless from the moment it exists, even though this
# is stricter than tests/test_boundary.py was previously required to check
# (02-PATTERNS.md flags this as a deliberate stricter-than-required choice).
NAVDATA_DIR = Path(__file__).resolve().parent.parent / "src" / "atc_sim" / "navdata"

# Matches `import pygame`, `import pygame.foo`, `import pygame as pg`,
# and `from pygame import ...` / `from pygame.foo import ...` forms.
PYGAME_IMPORT_RE = re.compile(r"^\s*(import\s+pygame(\.\w+)*(\s+as\s+\w+)?|from\s+pygame(\.\w+)*\s+import\b)")


def _iter_sim_python_files():
    return sorted(SIM_DIR.rglob("*.py"))


def _iter_navdata_python_files():
    return sorted(NAVDATA_DIR.rglob("*.py"))


def _find_pygame_import_violations(paths, relative_to):
    violations = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if PYGAME_IMPORT_RE.match(line):
                violations.append(f"{path.relative_to(relative_to)}:{lineno}: {stripped}")
    return violations


def test_sim_package_never_imports_pygame():
    """No module under src/atc_sim/sim/ may import pygame (CORE-03)."""
    violations = _find_pygame_import_violations(_iter_sim_python_files(), SIM_DIR.parent.parent.parent)

    assert not violations, (
        "src/atc_sim/sim/ must remain headless (CORE-03) but found pygame "
        "import(s):\n" + "\n".join(violations)
    )


def test_navdata_package_never_imports_pygame():
    """No module under src/atc_sim/navdata/ may import pygame. navdata is
    sim-core reference data (Runway/ILS/geo projection) shared with future
    separation math, so it must stay headlessly testable like sim/."""
    violations = _find_pygame_import_violations(_iter_navdata_python_files(), NAVDATA_DIR.parent.parent.parent)

    assert not violations, (
        "src/atc_sim/navdata/ must remain headless but found pygame "
        "import(s):\n" + "\n".join(violations)
    )
