# Agent Setup Contract

This file is the step-by-step setup and acceptance contract for **Dark Agent
Cad**. It is written to be followed by an AI coding agent after the human copies
the agent prompt from `README.md`.

## Operating rules

1. Work from the repository root.
2. Use **Python 3.12.x**. Do not use Python 3.13 or 3.14. AgentCAD 0.7.2
   requires Python `<3.13`; this project pins build123d 0.10.0 because AgentCAD
   0.7.2 requires build123d `<0.11`.
3. Create and use the local `cad-env/` virtual environment. Do not install these
   packages into the system Python.
4. Install from `requirements.txt`. Do not replace the pins with unpinned or
   latest versions.
5. Do not change the intended part geometry to make a validation pass. If a
   check fails, diagnose the environment or the build123d API usage, fix that,
   and rerun the check.
6. `cad-env/`, `exports/`, and `renders/` are local/generated and ignored by
   Git. Do not commit them.
7. If you find pre-existing user changes, preserve them. Do not clean or reset
   the worktree.

## 1. Detect the shell and Python

### Windows PowerShell

```powershell
py -0p
py -3.12 --version
```

Expected: `Python 3.12.x`.

If `py -3.12` is not available, install Python 3.12 for the current user:

```powershell
winget install --id Python.Python.3.12 -e --silent `
  --accept-package-agreements --accept-source-agreements --scope user
```

Open a new shell, then confirm:

```powershell
py -3.12 --version
```

### macOS / Linux

```bash
python3.12 --version
```

Expected: `Python 3.12.x`. If it is missing, install Python 3.12 with the
platform package manager or pyenv. For Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv
python3.12 --version
```

Do not continue with Python 3.13 or 3.14.

## 2. Create the virtual environment

### Windows PowerShell

```powershell
py -3.12 -m venv cad-env
.\cad-env\Scripts\python.exe -m pip install --upgrade pip
New-Item -ItemType Directory -Force -Path exports, renders | Out-Null
```

### macOS / Linux

```bash
python3.12 -m venv cad-env
./cad-env/bin/python -m pip install --upgrade pip
mkdir -p exports renders
```

Confirm that the environment uses Python 3.12:

```powershell
.\cad-env\Scripts\python.exe --version
```

```bash
./cad-env/bin/python --version
```

## 3. Install the pinned dependencies

### Windows PowerShell

```powershell
.\cad-env\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

### macOS / Linux

```bash
./cad-env/bin/python -m pip install --no-cache-dir -r requirements.txt
```

The pins are:

- `agentcad==0.7.2`
- `build123d==0.10.0`
- `ocp-vscode==4.2.0`
- `vtk==9.3.1`

Do not run `pip install build123d` without a version. The current resolver can
select a newer build123d that is incompatible with AgentCAD 0.7.2.

### If disk space runs out

Point the temporary directory and pip cache at a drive with room. On Windows:

```powershell
New-Item -ItemType Directory -Force -Path D:\cad-tmp | Out-Null
$env:TMP = 'D:\cad-tmp'
$env:TEMP = 'D:\cad-tmp'
.\cad-env\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

On macOS/Linux:

```bash
mkdir -p /path/with/space/cad-tmp
TMPDIR=/path/with/space/cad-tmp ./cad-env/bin/python -m pip install --no-cache-dir -r requirements.txt
```

If the virtual environment itself cannot fit on the current drive, create the
workspace on another drive and run the same commands from there.

## 4. Verify the environment

### Windows PowerShell

```powershell
.\cad-env\Scripts\python.exe -m pip check
.\cad-env\Scripts\python.exe -c "import sys, build123d, agentcad, ocp_vscode, vtk; print(sys.version); print(build123d.__version__, agentcad.__version__, ocp_vscode.__version__, vtk.vtkVersion.GetVTKVersion())"
```

### macOS / Linux

```bash
./cad-env/bin/python -m pip check
./cad-env/bin/python -c "import sys, build123d, agentcad, ocp_vscode, vtk; print(sys.version); print(build123d.__version__, agentcad.__version__, ocp_vscode.__version__, vtk.vtkVersion.GetVTKVersion())"
```

Expected:

```text
No broken requirements found.
3.12.x ...
0.10.0 0.7.2 4.2.0 9.3.1
```

`vtk` is used by the headless preview renderer. It is part of the pinned CAD
stack and is listed explicitly in `requirements.txt` so previews remain
reproducible.

## 5. Validate the example parts

Run all four checks from the repository root.

### Windows PowerShell

```powershell
.\cad-env\Scripts\python.exe scripts\runner.py scripts\template_part.py --expect exports\generated_bracket.step
.\cad-env\Scripts\python.exe scripts\runner.py scripts\handle.py --expect exports\handle.step
.\cad-env\Scripts\python.exe scripts\runner.py scripts\cooling_block.py --expect exports\cooling_block.step
.\cad-env\Scripts\python.exe scripts\runner.py scripts\p_trap.py --expect exports\p_trap.step
```

### macOS / Linux

```bash
./cad-env/bin/python scripts/runner.py scripts/template_part.py --expect exports/generated_bracket.step
./cad-env/bin/python scripts/runner.py scripts/handle.py --expect exports/handle.step
./cad-env/bin/python scripts/runner.py scripts/cooling_block.py --expect exports/cooling_block.step
./cad-env/bin/python scripts/runner.py scripts/p_trap.py --expect exports/p_trap.step
```

Each command must print a final `PASS` and exit with code `0`. The runner:

1. Parses the part script for syntax errors.
2. Executes the script inside `cad-env`.
3. Detects the STEP file created or updated in `exports/`.
4. Imports the STEP file back into OpenCascade.
5. Requires at least one solid that is valid, manifold/watertight,
   positive-volume, and has finite positive bounding-box dimensions.

Expected geometry:

| Part | Solids | Valid | Watertight | Volume (mm³) | Bounding box (mm) |
| --- | ---: | --- | --- | ---: | --- |
| Bracket | 1 | yes | yes | 49,207.345115 | 100 x 50 x 14 |
| Handle | 1 | yes | yes | 67,808.678012 | 180 x 34 x 57 |
| Cooling block | 1 | yes | yes | 170,270.571434 | 120 x 80 x 25 |
| P-trap | 1 | yes | yes | 269,165.016841 | 210.0 x 72.0 x 177.4 |

Small OpenCascade version differences can change the last few volume digits.
The hard requirements are: one valid, manifold solid, and the expected bounding
box. Treat volume as matching if it is within 0.1%.

Reports are written to:

- `renders/verification_report.json` — latest run, machine-readable.
- `renders/last_run.log` — latest run, console output.

## 6. Render the previews

This step is optional for geometry acceptance, but it is the expected
deliverable for a complete run. VTK renders offscreen, so no display is
required.

### Windows PowerShell

```powershell
.\cad-env\Scripts\python.exe scripts\render_step.py exports\handle.step renders\handle.png
.\cad-env\Scripts\python.exe scripts\render_step.py exports\cooling_block.step renders\cooling_block.png
.\cad-env\Scripts\python.exe scripts\render_step.py exports\cooling_block.step renders\cooling_block_section.png --cut-z 10 --elev 52 --azim -62
.\cad-env\Scripts\python.exe scripts\render_step.py exports\cooling_block.step renders\cooling_block_plan.png --cut-z 10 --elev 89.9 --azim -90
.\cad-env\Scripts\python.exe scripts\render_step.py exports\p_trap.step renders\p_trap.png --elev 12 --azim -60 --color 0.30 0.30 0.32
```

### macOS / Linux

```bash
./cad-env/bin/python scripts/render_step.py exports/handle.step renders/handle.png
./cad-env/bin/python scripts/render_step.py exports/cooling_block.step renders/cooling_block.png
./cad-env/bin/python scripts/render_step.py exports/cooling_block.step renders/cooling_block_section.png --cut-z 10 --elev 52 --azim -62
./cad-env/bin/python scripts/render_step.py exports/cooling_block.step renders/cooling_block_plan.png --cut-z 10 --elev 89.9 --azim -90
./cad-env/bin/python scripts/render_step.py exports/p_trap.step renders/p_trap.png --elev 12 --azim -60 --color 0.30 0.30 0.32
```

Confirm that each PNG exists and is non-empty. The section and plan views use a
Z = 10 mm clip, which exposes the internal channel.

## 7. Acceptance checklist

Mark an item complete only when the command actually succeeded.

- [ ] Python is 3.12.x.
- [ ] `cad-env/` exists and was created from Python 3.12.
- [ ] `pip check` reports no broken requirements.
- [ ] The environment imports `build123d`, `agentcad`, `ocp_vscode`, `vtk`, and
      the standard library `sys`.
- [ ] `build123d` is 0.10.0 and `agentcad` is 0.7.2.
- [ ] Bracket verification passes.
- [ ] Handle verification passes.
- [ ] Cooling block verification passes with the expected bounding box.
- [ ] P-trap verification passes with the expected bounding box.
- [ ] The four STEP files exist in `exports/` and are non-empty.
- [ ] The requested preview PNGs exist and are non-empty.
- [ ] No part geometry was changed just to make validation pass.
- [ ] Any deviations or failures are documented in the final report.

## 8. Required final report

Return a concise report in this format:

```text
STATUS: PASS or FAIL
OS/SHELL:
PYTHON:
PACKAGES: build123d=..., agentcad=..., ocp-vscode=..., vtk=...
PIP CHECK:
PARTS:
  bracket:       PASS/FAIL - solids=..., volume=..., bbox=...
  handle:        PASS/FAIL - solids=..., volume=..., bbox=...
  cooling_block: PASS/FAIL - solids=..., volume=..., bbox=...
  p_trap:        PASS/FAIL - solids=..., volume=..., bbox=...
ARTIFACTS:
  ...
DEVIATIONS:
  ...
```

If any check fails, set `STATUS: FAIL`, include the failing command and the
important error lines, list what you changed, and do not describe the run as
complete.

## 9. Troubleshooting

| Symptom | Cause and recovery |
| --- | --- |
| `No matching distribution found for agentcad` on Python 3.13/3.14 | AgentCAD 0.7.2 requires Python `<3.13`. Install Python 3.12, recreate `cad-env`, and reinstall from `requirements.txt`. |
| `Failed to establish a new connection` or a DNS error during `pip install` | pip cannot reach PyPI. Restore network/proxy access or use an internal wheel mirror, then rerun the pinned install. |
| The resolver installs build123d 0.13 and/or downgrades AgentCAD | Install the pinned `requirements.txt` in a fresh venv. Do not install `build123d` unpinned first. |
| `No space left on device` during installation | Set `TMP`/`TEMP` (Windows) or `TMPDIR` (POSIX) to a drive with room and retry with `--no-cache-dir`. Move the whole workspace if needed. |
| `CounterBoreHole` is not available inside `BuildSketch` | In build123d 0.10, `CounterBoreHole` is a `BuildPart` operation. Move it out of the sketch context and into `BuildPart`. |
| `AttributeError: 'Part' object has no attribute 'export_step'` | build123d 0.10 uses the function `export_step(shape, path)`, not the later method API. |
| `BRep_API: command not done` during a chamfer | Remove the non-essential cosmetic chamfer, keep the verified base geometry, and report the change. |
| A shape is valid but not manifold/watertight | Look for tangent or degenerate faces. Prefer a flat filleted cap or a robust boolean over tangent sphere caps; rerun the verifier after each geometry change. |
| `py -3.12` is not found after installation | Open a new shell. If it is still missing, use the full interpreter path, commonly `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`. |
| VTK preview fails in a headless environment | Offscreen VTK normally works; if the platform cannot create a context, report the preview as unavailable and still validate the STEP geometry. Do not mark the geometry check as failed because a preview failed. |

## 10. Geometry guardrails for future parts

- Keep export paths relative to the repository root, for example
  `exports/my_part.step`.
- Use `export_step(part.part, "exports/my_part.step")` with build123d 0.10.
- Keep the model as one solid unless the design explicitly calls for multiple
  bodies; the current verifier requires every solid to be valid and watertight.
- Avoid coincident/tangent faces at the limits of OpenCascade tolerances.
- Run `scripts/runner.py` after every geometry change and inspect
  `renders/verification_report.json` when a check fails.
- Use `scripts/render_step.py --cut-z <height>` to expose internal features
  without changing the model.
