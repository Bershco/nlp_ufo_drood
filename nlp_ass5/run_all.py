from __future__ import annotations

from .common import ensure_dirs
from . import drood, ufo


def main() -> None:
    ensure_dirs()
    drood.run()
    ufo.run()
    print("Done. See data/processed, outputs/figures, and outputs/reports.")


if __name__ == "__main__":
    main()
