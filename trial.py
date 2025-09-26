"""Legacy entrypoint kept for backwards compatible manual runs."""
from __future__ import annotations

import argparse
from collections.abc import Callable

from manual import (
    absence,
    assent,
    commerce,
    decline,
    fragments,
    rebuff,
    refuse,
    reliance,
    siren,
    surface,
    translation,
    veto,
    wording,
    override,
)

_SCENARIOS: dict[str, Callable[[], None]] = {
    "absence": absence,
    "assent": assent,
    "commerce": commerce,
    "decline": decline,
    "fragments": fragments,
    "rebuff": rebuff,
    "refuse": refuse,
    "reliance": reliance,
    "siren": siren,
    "surface": surface,
    "translation": translation,
    "veto": veto,
    "wording": wording,
    "override": override,
}


def run(name: str) -> None:
    """Execute manual scenario by name."""

    try:
        scenario = _SCENARIOS[name]
    except KeyError as error:  # pragma: no cover - convenience guard
        available = ", ".join(sorted(_SCENARIOS))
        raise SystemExit(f"Unknown scenario '{name}'. Available: {available}") from error
    scenario()


def main(argv: list[str] | None = None) -> None:
    """Parse command-line arguments and run the desired scenario."""

    parser = argparse.ArgumentParser(description=__doc__ or "Manual scenarios")
    parser.add_argument("scenario", choices=sorted(_SCENARIOS), help="Scenario name to run")
    args = parser.parse_args(argv)
    run(args.scenario)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()


__all__ = ["main", "run", *_SCENARIOS]
