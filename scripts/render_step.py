#!/usr/bin/env python3
"""Render a STEP file to a shaded PNG preview using VTK.

VTK gives correct depth occlusion for parts with internal cavities, unlike a
simple painter's-algorithm renderer. The renderer is headless and uses the VTK
wheel already installed as part of the CAD dependency stack.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import vtk
from build123d import Align, Box, Pos, import_step
from vtk.util.numpy_support import numpy_to_vtk


def _clip_below(shape, cut_z: float):
    """Keep only the portion of a shape below a horizontal section plane."""
    bounds = shape.bounding_box()
    if cut_z <= bounds.min.Z or cut_z >= bounds.max.Z:
        return shape
    height = cut_z - bounds.min.Z
    clip = Pos(
        bounds.center().X,
        bounds.center().Y,
        bounds.min.Z - 0.5,
    ) * Box(
        bounds.size.X + 2.0,
        bounds.size.Y + 2.0,
        height + 0.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return shape & clip


def render_step(
    step_path: Path,
    output_path: Path,
    tolerance: float = 0.2,
    cut_z: float | None = None,
    elev: float = 24.0,
    azim: float = -55.0,
    width_px: int = 1600,
    height_px: int = 1100,
    color: tuple[float, float, float] = (0.52, 0.64, 0.76),
) -> None:
    shape = import_step(str(step_path))
    if cut_z is not None:
        shape = _clip_below(shape, cut_z)

    vertices, triangles = shape.tessellate(tolerance, 0.2)
    if not triangles:
        raise RuntimeError(f"No triangles generated for {step_path}")

    points_np = np.array(
        [[vertex.X, vertex.Y, vertex.Z] for vertex in vertices], dtype=np.float64
    )
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(points_np, deep=True))

    cells = vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3)
        for index in triangle:
            cells.InsertCellPoint(int(index))

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(polydata)
    normals.ComputePointNormalsOn()
    normals.ComputeCellNormalsOn()
    normals.SplittingOff()
    normals.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetAmbient(0.22)
    actor.GetProperty().SetDiffuse(0.78)
    actor.GetProperty().SetSpecular(0.35)
    actor.GetProperty().SetSpecularPower(35)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)
    renderer.AddActor(actor)

    light_kit = vtk.vtkLightKit()
    light_kit.SetKeyLightIntensity(0.88)
    light_kit.AddLightsToRenderer(renderer)

    minimum = points_np.min(axis=0)
    maximum = points_np.max(axis=0)
    center = (minimum + maximum) / 2.0
    diagonal = float(np.linalg.norm(maximum - minimum))
    direction = np.array(
        [
            np.cos(np.deg2rad(elev)) * np.cos(np.deg2rad(azim)),
            np.cos(np.deg2rad(elev)) * np.sin(np.deg2rad(azim)),
            np.sin(np.deg2rad(elev)),
        ]
    )

    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(*center)
    camera.SetPosition(*(center + direction * diagonal * 2.2))
    camera.SetViewUp(0, 0, 1)
    camera.SetViewAngle(30)
    renderer.ResetCameraClippingRange()

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetMultiSamples(0)
    window.SetSize(width_px, height_px)
    window.AddRenderer(renderer)
    window.Render()

    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetScale(1)
    capture.ReadFrontBufferOff()
    capture.Update()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a STEP file to PNG.")
    parser.add_argument("step", help="Input STEP file")
    parser.add_argument("png", help="Output PNG file")
    parser.add_argument(
        "--tolerance", type=float, default=0.2, help="Tessellation tolerance (mm)"
    )
    parser.add_argument(
        "--cut-z",
        type=float,
        default=None,
        help="Keep only geometry below this Z height (section view)",
    )
    parser.add_argument("--elev", type=float, default=24.0, help="View elevation")
    parser.add_argument("--azim", type=float, default=-55.0, help="View azimuth")
    parser.add_argument(
        "--color",
        nargs=3,
        type=float,
        metavar=("R", "G", "B"),
        default=(0.52, 0.64, 0.76),
        help="Actor color as three 0-1 RGB values",
    )
    args = parser.parse_args()

    render_step(
        Path(args.step),
        Path(args.png),
        tolerance=args.tolerance,
        cut_z=args.cut_z,
        elev=args.elev,
        azim=args.azim,
        color=tuple(args.color),
    )
    print(f"Rendered {args.step} -> {args.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
