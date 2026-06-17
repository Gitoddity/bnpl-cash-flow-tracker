from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from bnpl_cashflow.application import run_application
from bnpl_cashflow.input import InputValidationError, parse_json_payload
from bnpl_cashflow.reporting import render_application_report


def main(argv: list[str] | None = None, *, stdin: TextIO | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    parser = argparse.ArgumentParser(prog="bnpl_cashflow")
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to a JSON file. Omit or use '-' to read from stdin.",
    )

    args = parser.parse_args(argv)

    try:
        raw_payload = _read_input(args.input_path, stdin)
    except OSError:
        print("Unable to read input file.", file=stderr)
        return 1

    try:
        validated_payload = parse_json_payload(raw_payload)
    except InputValidationError as exc:
        _print_validation_errors(exc, stderr)
        return 1
    except (json.JSONDecodeError, ValueError, TypeError):
        print("Invalid JSON input.", file=stderr)
        return 1

    try:
        application_result = run_application(validated_payload)
        report = render_application_report(application_result)
    except Exception:
        print("An unexpected runtime error occurred.", file=stderr)
        return 1

    print(report, file=stdout)
    return 0


def _read_input(input_path: str | None, stdin: TextIO) -> str:
    if input_path in (None, "-"):
        return stdin.read()

    return Path(input_path).read_text(encoding="utf-8")


def _print_validation_errors(error: InputValidationError, stderr: TextIO) -> None:
    print("Validation failed:", file=stderr)
    for issue in error.issues:
        print(f"- {issue.format()}", file=stderr)


if __name__ == "__main__":
    raise SystemExit(main())

