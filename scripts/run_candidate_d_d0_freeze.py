#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.candidate_d_baseline import build_d0_artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=ROOT)
    args = parser.parse_args()
    decision = build_d0_artifacts(args.root, args.out)
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
