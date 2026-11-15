# Optional Browser Viewer

This folder contains an **optional** interactive viewer for the checked-in
`examples/*.step` files. It is separate from the Python CAD environment and is
not required to build, validate, or render parts.

## What `online-3d-viewer` is

[`online-3d-viewer`](https://www.npmjs.com/package/online-3d-viewer) is the
open-source browser engine behind [3dviewer.net](https://3dviewer.net). It is a
JavaScript library, not a command-line converter:

- It imports STEP, IGES, BREP, STL, OBJ, PLY, GLTF, and several other formats in
  the browser.
- It provides the orbit/pan/zoom canvas used by the viewer page.
- It is MIT licensed. The project pins version `0.18.0`.

The viewer page loads the package's prebuilt browser bundle from
`viewer/node_modules/`. No Vite or other bundler is required.

STEP import uses `occt-import-js`, which the engine downloads from jsDelivr the
first time a STEP file is opened. The viewer therefore needs internet access for
STEP import. For fully offline review, use the VTK PNG previews produced by
`scripts/render_step.py`.

## Agent approval gate

An agent must **not** install this viewer automatically. Before running
`npm install`, the agent must ask the human with its question tool, for example:

```text
Install the optional Online 3D Viewer?
It adds Node.js/npm dependencies in viewer/ and enables interactive STEP
inspection in a browser. It is not needed for CAD verification or VTK previews.
[Install] [Skip]
```

Proceed only if the human chooses **Install**. If they choose **Skip**, leave
`viewer/node_modules/` absent and continue with the Python workflow.

## Install

Prerequisite: Node.js and npm. Node.js 20 or newer is recommended. On Windows,
if PowerShell blocks `npm.ps1`, use `npm.cmd` instead.

```powershell
cd viewer
npm install
cd ..
```

For a clean install from the committed lockfile, use `npm ci` instead of
`npm install`. Or, from the repository root:

```powershell
npm.cmd --prefix viewer install
```

## Run

Serve the **repository root**, not just the `viewer` folder. The page loads
models from `../examples/` and expects an HTTP origin.

```powershell
.\cad-env\Scripts\python.exe viewer\serve.py
```

On macOS/Linux:

```bash
./cad-env/bin/python viewer/serve.py
```

Open <http://127.0.0.1:8000/viewer/>. The script opens it automatically unless
you pass `--no-browser`.

You can also use any static server from the repository root:

```powershell
python -m http.server 8000
```

Then open <http://127.0.0.1:8000/viewer/>. Do not double-click
`viewer/index.html`; the `file://` origin cannot load the STEP files.

## Using the page

- Choose one of the four checked-in examples from the **Example** menu.
- Use **Open local model** to inspect a `.step`, `.stp`, or mesh file from your
  computer. Selecting multiple files is supported for formats that reference
  sidecar files such as OBJ/MTL.
- Drag to orbit, scroll to zoom, and right-drag to pan.
- **Reload current model** re-imports the current file, which also refits the
  camera.

## Troubleshooting

| Symptom | Recovery |
| --- | --- |
| `Viewer engine not installed` | Run `cd viewer` then `npm install`; restart the server. |
| Blank page or 404 for `o3dv.min.js` | Start the server from the repository root so `/viewer/node_modules/...` resolves. |
| STEP stays on `Importing model...` | The `occt-import-js` import is fetched from jsDelivr. Check internet access and the browser console. Use `render_step.py` for offline review. |
| `npm.ps1 cannot be loaded` | Use `npm.cmd` or adjust the PowerShell execution policy for your user. |
| Port 8000 is busy | Run `python viewer/serve.py --port 8010` and open the printed URL. |
| A large model is slow | STEP tessellation happens in the browser; use the VTK preview for a quick image. |

## Skip it

If you do not need interactive inspection, do not install Node.js or run npm.
The pinned Python environment, `scripts/runner.py`, and
`scripts/render_step.py` are the supported path.
