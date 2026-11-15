/**
 * Optional browser viewer for the checked-in Dark Agent Cad examples.
 *
 * The engine is loaded as the prebuilt `OV` browser bundle from
 * `viewer/node_modules/online-3d-viewer`. STEP import is handled by
 * `occt-import-js`, which the engine fetches from jsDelivr on first use.
 */
(() => {
  const EXAMPLES = {
    p_trap: { label: "P-trap fitting", file: "p_trap.step" },
    cooling_block: { label: "Liquid-cooling block", file: "cooling_block.step" },
    handle: { label: "Pull handle", file: "handle.step" },
    bracket: { label: "Reference bracket", file: "bracket.step" },
  };

  const parent = document.getElementById("viewer");
  const status = document.getElementById("status");
  const modelSelect = document.getElementById("model-select");
  const fileInput = document.getElementById("file-input");
  const reloadButton = document.getElementById("reload-model");

  let viewer = null;
  let currentUrls = null;
  let currentFiles = null;
  let currentLabel = "";

  const setStatus = (message, isError = false) => {
    status.textContent = message;
    status.classList.toggle("error", isError);
    parent.setAttribute("aria-busy", isError ? "false" : "true");
  };

  const disableControls = () => {
    [modelSelect, fileInput, reloadButton].forEach((control) => {
      if (control) {
        control.disabled = true;
      }
    });
  };

  if (!window.OV) {
    disableControls();
    setStatus(
      "Viewer engine not installed. Run `cd viewer` then `npm install`, and serve the repo root (for example `python viewer/serve.py`).",
      true,
    );
    return;
  }

  const formatModelInfo = () => {
    try {
      const meshCount = viewer.model && viewer.model.MeshCount
        ? viewer.model.MeshCount()
        : null;
      return meshCount === null ? "" : ` (${meshCount} mesh${meshCount === 1 ? "" : "es"})`;
    } catch {
      return "";
    }
  };

  const finishLoad = () => {
    const label = currentLabel || "model";
    setStatus(`Loaded ${label}${formatModelInfo()}.`);
    parent.setAttribute("aria-busy", "false");
    document.title = `Dark Agent Cad Viewer - ${label}`;
  };

  const failLoad = () => {
    setStatus(
      "Could not load the model. For STEP files, the first import needs internet access to fetch occt-import-js from jsDelivr. Check the browser console and try again.",
      true,
    );
    parent.setAttribute("aria-busy", "false");
  };

  viewer = new OV.EmbeddedViewer(parent, {
    backgroundColor: new OV.RGBAColor(255, 255, 255, 255),
    defaultColor: new OV.RGBColor(92, 113, 138),
    defaultLineColor: new OV.RGBColor(36, 45, 56),
    edgeSettings: new OV.EdgeSettings(true, new OV.RGBColor(36, 45, 56), 20),
    environmentSettings: new OV.EnvironmentSettings([], false),
    onModelLoaded: finishLoad,
    onModelLoadFailed: failLoad,
  });

  const loadExample = (id) => {
    const example = EXAMPLES[id];
    if (!example) {
      return;
    }

    currentFiles = null;
    currentLabel = example.label;
    currentUrls = [new URL(`../examples/${example.file}`, window.location.href).href];
    setStatus(`Loading ${example.label}...`);
    viewer.LoadModelFromUrlList(currentUrls);
  };

  const loadFiles = (files) => {
    if (!files || files.length === 0) {
      return;
    }

    currentUrls = null;
    currentFiles = Array.from(files);
    currentLabel = currentFiles.map((file) => file.name).join(", ");
    setStatus(`Loading ${currentLabel}...`);
    viewer.LoadModelFromFileList(currentFiles);
  };

  modelSelect.addEventListener("change", () => {
    loadExample(modelSelect.value);
  });

  fileInput.addEventListener("change", () => {
    loadFiles(fileInput.files);
    fileInput.value = "";
  });

  reloadButton.addEventListener("click", () => {
    if (currentFiles) {
      setStatus(`Reloading ${currentLabel}...`);
      viewer.LoadModelFromFileList(currentFiles);
    } else if (currentUrls) {
      setStatus(`Reloading ${currentLabel}...`);
      viewer.LoadModelFromUrlList(currentUrls);
    } else {
      loadExample(modelSelect.value);
    }
  });

  loadExample(modelSelect.value);
})();
