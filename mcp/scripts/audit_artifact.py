#!/usr/bin/env python3
"""Audit a built connector wheel before attaching it to a release."""

from __future__ import annotations

import argparse
import json

from knowb_org_index.artifacts import audit_wheel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel")
    args = parser.parse_args()
    print(json.dumps(audit_wheel(args.wheel), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
