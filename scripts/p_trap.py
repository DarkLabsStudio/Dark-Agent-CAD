"""Hollow P-trap plumbing fitting with union nuts.

The reference is a black plastic 1-1/2 inch tubular P-trap. This model uses a
42 mm outside diameter pipe with a 3 mm wall, a 120 mm centerline U-bend, a
vertical inlet, a 45 degree outlet elbow, and ribbed union nuts at both ends.
A slip ring with a mounting tab wraps the right-hand leg.

The pipe is a swept annular section, so the finished part is hollow and open at
both union nuts. The nuts and slip ring overlap the pipe wall slightly so the
whole assembly is one valid, watertight solid.
"""

from math import cos, radians, sin

from build123d import *

# Pipe and centerline
PIPE_OD = 42.0
PIPE_WALL = 3.0
PIPE_RADIUS = PIPE_OD / 2
PIPE_BORE_RADIUS = PIPE_RADIUS - PIPE_WALL

LEFT_X = -60.0
RIGHT_X = 60.0
U_CENTER_Z = 80.0
U_RADIUS = 60.0
LEFT_TOP_Z = 170.0
RIGHT_TOP_Z = 110.0

ELBOW_RADIUS = 30.0
OUTLET_ANGLE = 45.0
OUTLET_LENGTH = 30.0

# Union nuts
NUT_OUTER_RADIUS = 34.0
NUT_HEIGHT = 24.0
NUT_BORE_RADIUS = PIPE_RADIUS - 0.2
NUT_FLANGE_RADIUS = 36.0
NUT_FLANGE_HEIGHT = 4.0
NUT_GROOVE_RADIUS = 1.8
NUT_GROOVES = 14

# Slip ring and mounting tab on the outlet leg
SLIP_RING_RADIUS = 27.0
SLIP_RING_HEIGHT = 10.0
SLIP_Z = RIGHT_TOP_Z - 15.0
SLIP_TAB_X = 12.0
SLIP_TAB_Y = 12.0
SLIP_TAB_Z = 8.0
SLIP_TAB_Y_CENTER = -30.0
SLIP_TAB_HOLE_RADIUS = 1.8


def make_union_nut(plane: Plane) -> Part:
    """Build a ribbed union nut whose local +Z follows the given plane."""
    with BuildPart(plane) as nut:
        Cylinder(
            NUT_OUTER_RADIUS,
            NUT_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # A thin flange at the pipe side of the nut.
        with Locations((0, 0, -NUT_FLANGE_HEIGHT)):
            Cylinder(
                NUT_FLANGE_RADIUS,
                NUT_FLANGE_HEIGHT + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Through-bore. It is 0.2 mm smaller than the pipe OD so the nut and
        # pipe overlap rather than merely touching at a coincident face.
        with Locations((0, 0, -NUT_FLANGE_HEIGHT - 1.0)):
            Cylinder(
                NUT_BORE_RADIUS,
                NUT_HEIGHT + NUT_FLANGE_HEIGHT + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Shallow axial scallops form the grip ribs.
        with PolarLocations(NUT_OUTER_RADIUS, NUT_GROOVES):
            Cylinder(
                NUT_GROOVE_RADIUS,
                NUT_HEIGHT + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return nut.part


def make_p_trap_path() -> Curve:
    """Return the planar centerline of the trap, starting at the inlet."""
    with BuildLine(Plane.XZ) as path:
        Line((LEFT_X, LEFT_TOP_Z), (LEFT_X, U_CENTER_Z))
        CenterArc((0, U_CENTER_Z), U_RADIUS, 180, 180)
        Line((RIGHT_X, U_CENTER_Z), (RIGHT_X, RIGHT_TOP_Z))
        CenterArc(
            (RIGHT_X + ELBOW_RADIUS, RIGHT_TOP_Z),
            ELBOW_RADIUS,
            180,
            -OUTLET_ANGLE,
        )

        arc_end = (
            RIGHT_X
            + ELBOW_RADIUS
            + ELBOW_RADIUS * cos(radians(180 - OUTLET_ANGLE)),
            RIGHT_TOP_Z + ELBOW_RADIUS * sin(radians(180 - OUTLET_ANGLE)),
        )
        outlet_end = (
            arc_end[0] + OUTLET_LENGTH * cos(radians(OUTLET_ANGLE)),
            arc_end[1] + OUTLET_LENGTH * sin(radians(OUTLET_ANGLE)),
        )
        Line(arc_end, outlet_end)

    return path.line


def make_slip_ring() -> Part:
    """Build the clamp ring on the right leg, including its mounting tab."""
    with BuildPart(Plane(origin=(RIGHT_X, 0, SLIP_Z), z_dir=(0, 0, 1))) as ring:
        Cylinder(
            SLIP_RING_RADIUS,
            SLIP_RING_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations((0, 0, -1.0)):
            Cylinder(
                NUT_BORE_RADIUS,
                SLIP_RING_HEIGHT + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # The tab faces the front of the default preview camera.
        with Locations((0, SLIP_TAB_Y_CENTER, SLIP_RING_HEIGHT / 2)):
            Box(SLIP_TAB_X, SLIP_TAB_Y, SLIP_TAB_Z)
            Cylinder(
                SLIP_TAB_HOLE_RADIUS,
                SLIP_TAB_Y + 4.0,
                rotation=(90, 0, 0),
                mode=Mode.SUBTRACT,
            )

    return ring.part


def generate_p_trap() -> Part:
    path = make_p_trap_path()
    path_end = path @ 1
    path_axis = path % 1

    with BuildPart() as trap:
        # Sweep an annular section along the centerline to make a hollow pipe.
        with BuildSketch(
            Plane(origin=(LEFT_X, 0, LEFT_TOP_Z), z_dir=(0, 0, -1))
        ) as section:
            Circle(PIPE_RADIUS)
            Circle(PIPE_BORE_RADIUS, mode=Mode.SUBTRACT)
        sweep(path=path)

        # Inlet union nut, at the top of the left leg.
        add(
            make_union_nut(
                Plane(
                    origin=(LEFT_X, 0, LEFT_TOP_Z - NUT_HEIGHT),
                    z_dir=(0, 0, 1),
                )
            )
        )

        # Outlet union nut, aligned with the 45 degree outlet.
        add(
            make_union_nut(
                Plane(
                    origin=path_end - path_axis * NUT_HEIGHT,
                    z_dir=path_axis,
                )
            )
        )

        # Slip ring on the right leg.
        add(make_slip_ring())

    return trap.part


if __name__ == "__main__":
    part = generate_p_trap()
    export_step(part, "exports/p_trap.step")
    print("P-trap compiled and exported to exports/p_trap.step")
    print(f"Volume: {part.volume:.2f} mm^3")
