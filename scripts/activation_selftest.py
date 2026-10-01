#!/usr/bin/env python3
"""Verify the offline activation derivation without exposing its input on argv."""

from __future__ import annotations

import argparse
import getpass
import sys

from dentiva.security.activation import VERIFICATION_DIGEST, derive_activation_digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit-digest",
        action="store_true",
        help="print the derived digest for an owner-authorized verifier rotation",
    )
    args = parser.parse_args()
    candidate = getpass.getpass("Activation input (not echoed): ")
    digest = derive_activation_digest(candidate)
    if args.emit_digest:
        print(digest.hex())
        return 0
    if digest != VERIFICATION_DIGEST:
        print("Activation self-test did not match the shipped verifier.", file=sys.stderr)
        return 1
    print("Activation derivation matches the compiled verifier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
