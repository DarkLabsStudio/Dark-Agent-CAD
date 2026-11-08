#!/usr/bin/env python3
"""Compile and verify build123d part scripts inside the isolated CAD env.

Usage
-----
    python scripts/runner.py scripts/template_part.py
    python scripts/runner.py scripts/part.py --expect exports/part.step
    python scripts/runner.py scripts/part.py --timeout 120 --json

The runner:
  1. Re-executes itself with ``cad-env`` if launched by another interpreter.
  2. Performs an immediate syntax check with ``compile()``.
  3. Runs the target script as a subprocess, capturing stdout and stderr.
  4. Finds every STEP file created or modified by the run.
  5. Re-imports each STEP file and checks solid validity, manifold/watertight
     topology, positive volume, finite dimensions, and bounding box.
  6. Writes a machine-readable report to ``renders/verification_report.json``.

Exit code 0 means every check passed; any failure returns a non-zero code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
VENV_PYTHON = (
    WORKSPACE
    / "cad-env"
    / ("Scripts" if os.name == "nt" else "bin")
    / ("python.exe" if os.name == "nt" else "python")
)
EXPORTS_DIR = WORKSPACE / "exports"
RENDERS_DIR = WORKSPACE / "renders"
REPORT_PATH = RENDERS_DIR / "verification_report.json"
LOG_PATH = RENDERS_DIR / "last_run.log"
STEP_SUFFIXES = {".step", ".stp"}


def _reconfigure_console() -> None:
    """Make Windows consoles tolerate UTF-8 output from CAD scripts."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def _ensure_venv() -> None:
    """Guarantee the runner and target execute with the workspace interpreter."""
    if not VENV_PYTHON.exists():
        return
    try:
        already_isolated = Path(sys.executable).resolve() == VENV_PYTHON.resolve()
    except OSError:
        already_isolated = False
    if not already_isolated:
        raise SystemExit(
            subprocess.call(
                [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
            )
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_steps() -> dict[str, dict[str, Any]]:
    """Hash every STEP file currently present in exports/."""
    snapshot: dict[str, dict[str, Any]] = {}
    if not EXPORTS_DIR.exists():
        return snapshot
    for path in sorted(EXPORTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in STEP_SUFFIXES:
            continue
        stat = path.stat()
        snapshot[str(path.relative_to(WORKSPACE))] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": _sha256(path),
        }
    return snapshot


def _select_steps(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    expected: list[str],
) -> tuple[list[Path], list[str]]:
    """Return (files to validate, missing explicit expectations)."""
    selected: list[Path] = []
    missing: list[str] = []

    for item in expected:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = WORKSPACE / candidate
        candidate = candidate.resolve()
        if candidate.exists():
            if candidate not in selected:
                selected.append(candidate)
        else:
            missing.append(str(candidate))

    for relative, metadata in after.items():
        previous = before.get(relative)
        changed = (
            previous is None
            or previous["sha256"] != metadata["sha256"]
            or previous["size"] != metadata["size"]
            or previous["mtime_ns"] != metadata["mtime_ns"]
        )
        if not changed:
            continue
        candidate = (WORKSPACE / relative).resolve()
        if candidate not in selected:
            selected.append(candidate)

    return selected, missing


def _validate_step(path: Path) -> dict[str, Any]:
    """Import one STEP file and verify its topology is usable engineering geometry."""
    info: dict[str, Any] = {
        "path": str(path),
        "relative_path": str(path.relative_to(WORKSPACE)) if path.is_relative_to(WORKSPACE) else str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "ok": False,
        "errors": [],
    }
    errors: list[str] = info["errors"]

    if not path.exists():
        errors.append("STEP file does not exist")
        return info
    if info["size_bytes"] <= 0:
        errors.append("STEP file is empty")
        return info

    try:
        header = path.read_bytes()[:4096].lstrip()
    except OSError as exc:
        errors.append(f"cannot read STEP file: {exc}")
        return info
    if not header.upper().startswith(b"ISO-10303-21"):
        errors.append("file is not an ISO-10303-21 STEP exchange file")

    try:
        from build123d import import_step
    except Exception as exc:  # pragma: no cover - environment failure
        errors.append(f"cannot import build123d: {exc}")
        return info

    try:
        shape = import_step(str(path))
    except Exception as exc:
        errors.append(f"STEP import failed: {type(exc).__name__}: {exc}")
        return info

    if shape is None:
        errors.append("STEP importer returned no shape")
        return info

    try:
        solids = list(shape.solids())
        info["solids"] = len(solids)
        info["faces"] = len(shape.faces())
        info["edges"] = len(shape.edges())

        if not solids:
            errors.append("shape contains no solids")

        valid = bool(solids) and all(bool(solid.is_valid) for solid in solids)
        manifold = bool(solids) and all(bool(solid.is_manifold) for solid in solids)
        volume = sum(float(solid.volume) for solid in solids)
        bbox = shape.bounding_box()
        bbox_size = bbox.size

        info.update(
            {
                "valid": valid,
                "manifold": manifold,
                "watertight": bool(valid and manifold and solids),
                "volume_mm3": round(volume, 6),
                "bbox_mm": {
                    "x": round(float(bbox_size.X), 6),
                    "y": round(float(bbox_size.Y), 6),
                    "z": round(float(bbox_size.Z), 6),
                },
                "bbox_min_mm": {
                    "x": round(float(bbox.min.X), 6),
                    "y": round(float(bbox.min.Y), 6),
                    "z": round(float(bbox.min.Z), 6),
                },
                "bbox_max_mm": {
                    "x": round(float(bbox.max.X), 6),
                    "y": round(float(bbox.max.Y), 6),
                    "z": round(float(bbox.max.Z), 6),
                },
            }
        )

        if not valid:
            errors.append("OpenCascade reports an invalid or self-intersecting solid")
        if not manifold:
            errors.append("solid is not watertight (an edge does not border exactly two faces)")
        if not math.isfinite(volume) or volume <= 0:
            errors.append(f"solid volume must be finite and positive, got {volume!r}")
        for axis, value in (("X", bbox_size.X), ("Y", bbox_size.Y), ("Z", bbox_size.Z)):
            if not math.isfinite(float(value)) or float(value) <= 0:
                errors.append(f"bounding-box {axis} extent must be positive, got {value!r}")
    except Exception as exc:
        errors.append(f"geometric inspection failed: {type(exc).__name__}: {exc}")

    info["ok"] = not errors
    return info


def _print_stream(label: str, text: str, limit: int = 300) -> None:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").rstrip().splitlines()
    if not lines:
        return
    print(f"--- {label} ({len(lines)} line{'s' if len(lines) != 1 else ''}) ---")
    for line in lines[:limit]:
        print(f"  {line}")
    if len(lines) > limit:
        print(f"  ... {len(lines) - limit} more line(s) omitted from console output")


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "=" * 74,
        "CAD VERIFICATION SUMMARY",
        "=" * 74,
        f"Script      : {report['script']}",
        f"Interpreter : {report['python_version']}",
        f"Executable  : {report['executable']}",
        f"Exit code   : {report['exit_code']}",
        f"Duration    : {report['duration_s']:.2f}s",
        f"Result      : {report['result']}",
    ]
    if report["missing_expectations"]:
        lines.append("Missing expected STEP file(s):")
        lines.extend(f"  - {item}" for item in report["missing_expectations"])
    lines.append("STEP artifacts:")
    if not report["steps"]:
        lines.append("  (none)")
    for step in report["steps"]:
        lines.extend(
            [
                f"  - {step['relative_path']}",
                f"      size       : {step['size_bytes']:,} bytes",
                f"      solids     : {step.get('solids', 'n/a')}",
                f"      valid      : {step.get('valid', False)}",
                f"      manifold   : {step.get('manifold', False)}",
                f"      watertight : {step.get('watertight', False)}",
                f"      volume     : {step.get('volume_mm3', 'n/a')} mm^3",
                f"      bbox       : {step.get('bbox_mm', 'n/a')} mm",
            ]
        )
        for error in step.get("errors", []):
            lines.append(f"      ERROR      : {error}")
    lines.extend(
        [
            f"Report      : {report['report_path']}",
            f"Log         : {report['log_path']}",
            "=" * 74,
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _reconfigure_console()
    _ensure_venv()

    parser = argparse.ArgumentParser(
        description="Compile and verify a build123d part inside cad-env."
    )
    parser.add_argument("script", help="Part script to execute (e.g. scripts/template_part.py)")
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        metavar="STEP",
        help="STEP file expected from the run; may be repeated",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Maximum execution time in seconds (default: 300)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON report in addition to the summary",
    )
    args = parser.parse_args(argv)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)

    script = Path(args.script)
    if not script.is_absolute():
        script = (Path.cwd() / script).resolve()
    if not script.exists():
        fallback = (WORKSPACE / args.script).resolve()
        if fallback.exists():
            script = fallback
    if not script.is_file():
        print(f"ERROR: script not found: {args.script}", file=sys.stderr)
        return 1

    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    print("=" * 74)
    print("CAD COMPILATION / GEOMETRY VERIFICATION")
    print("=" * 74)
    print(f"Workspace : {WORKSPACE}")
    print(f"Script    : {script}")
    print(f"Python    : {sys.version.split()[0]} ({sys.executable})")
    print()

    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timed_out = False

    # 1. Syntax gate -----------------------------------------------------
    print("[1/4] Syntax check")
    try:
        source = script.read_text(encoding="utf-8")
        compile(source, str(script), "exec")
        print("      PASS - source parses as valid Python")
    except SyntaxError as exc:
        location = f"{exc.filename}:{exc.lineno}:{exc.offset}"
        print(f"      FAIL - {location}: {exc.msg}")
        report = {
            "timestamp": started_at,
            "script": str(script),
            "python_version": sys.version.split()[0],
            "executable": sys.executable,
            "exit_code": 1,
            "timed_out": False,
            "duration_s": time.perf_counter() - started,
            "syntax_ok": False,
            "stdout": "",
            "stderr": "",
            "steps": [],
            "missing_expectations": [],
            "result": "FAIL",
            "report_path": str(REPORT_PATH),
            "log_path": str(LOG_PATH),
        }
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        LOG_PATH.write_text(_render_summary(report), encoding="utf-8")
        print()
        print(_render_summary(report))
        return 1
    except OSError as exc:
        print(f"      FAIL - cannot read script: {exc}")
        return 1

    # 2. Isolated execution ---------------------------------------------
    print()
    print("[2/4] Execute inside cad-env")
    before = _snapshot_steps()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["CAD_AGENT_WORKSPACE"] = str(WORKSPACE)
    python_paths = [str(WORKSPACE), str(script.parent)]
    if env.get("PYTHONPATH"):
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    try:
        process = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(WORKSPACE),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
        )
        stdout = process.stdout or ""
        stderr = process.stderr or ""
        exit_code = process.returncode
        if exit_code == 0:
            print("      PASS - process exited with code 0")
        else:
            print(f"      FAIL - process exited with code {exit_code}")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = -1
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        print(f"      FAIL - execution exceeded {args.timeout:g}s timeout")
    except OSError as exc:
        exit_code = -1
        stderr = f"{type(exc).__name__}: {exc}"
        print(f"      FAIL - could not start interpreter: {exc}")

    print()
    _print_stream("stdout", stdout)
    _print_stream("stderr", stderr)

    # 3. Artifact discovery ---------------------------------------------
    print()
    print("[3/4] STEP artifact discovery")
    after = _snapshot_steps()
    step_files, missing_expectations = _select_steps(before, after, args.expect)
    if missing_expectations:
        for item in missing_expectations:
            print(f"      MISSING - {item}")
    if step_files:
        for path in step_files:
            print(f"      FOUND   - {path}")
    else:
        print("      FAIL - no STEP file was created or updated in exports/")

    # 4. Geometric validation -------------------------------------------
    print()
    print("[4/4] Watertight geometry validation")
    step_reports: list[dict[str, Any]] = []
    for path in step_files:
        result = _validate_step(path)
        step_reports.append(result)
        status = "PASS" if result["ok"] else "FAIL"
        print(f"      {status} - {path.name}")
        if result["ok"]:
            print(
                f"             solids={result.get('solids')} "
                f"volume={result.get('volume_mm3')} mm^3 "
                f"bbox={result.get('bbox_mm')} mm"
            )
        for error in result["errors"]:
            print(f"             ERROR: {error}")

    execution_ok = exit_code == 0 and not timed_out
    artifacts_ok = bool(step_files) and not missing_expectations
    geometry_ok = bool(step_reports) and all(item["ok"] for item in step_reports)
    passed = execution_ok and artifacts_ok and geometry_ok

    report = {
        "timestamp": started_at,
        "script": str(script),
        "python_version": sys.version.split()[0],
        "executable": sys.executable,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_s": round(time.perf_counter() - started, 3),
        "syntax_ok": True,
        "stdout": stdout,
        "stderr": stderr,
        "steps": step_reports,
        "missing_expectations": missing_expectations,
        "result": "PASS" if passed else "FAIL",
        "report_path": str(REPORT_PATH),
        "log_path": str(LOG_PATH),
    }
    report_json = json.dumps(report, indent=2)
    REPORT_PATH.write_text(report_json, encoding="utf-8")
    LOG_PATH.write_text(_render_summary(report), encoding="utf-8")

    print()
    print(_render_summary(report))
    if args.json:
        print()
        print(report_json)

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
