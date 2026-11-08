"""Parametric pull handle for a drawer, door, or equipment panel.

Geometry
--------
- Overall length: 180 mm
- Overall height: 57 mm
- Grip: 18 mm diameter, 180 mm long, with 2.5 mm edge rounds
- Two 15 mm diameter posts at +/-60 mm
- Two 34 mm diameter mounting bases, 6 mm tall
- Four M4 clearance holes with 7 mm counterbores, 3 mm deep

The mounting bases sit on the panel; the counterbored holes face upward so
socket-head screws can be installed from the front of the handle.
"""

from build123d import *

# Primary dimensions (mm)
GRIP_RADIUS = 9.0
GRIP_LENGTH = 180.0
GRIP_Z = 48.0
POST_RADIUS = 7.5
POST_HEIGHT = GRIP_Z - 6.0
POST_X = 60.0
BASE_RADIUS = 17.0
BASE_HEIGHT = 6.0
SCREW_HOLE_RADIUS = 2.25  # M4 clearance
COUNTERBORE_RADIUS = 3.5
COUNTERBORE_DEPTH = 3.0
SCREW_Y = 11.5
GRIP_END_FILLET = 2.5


def generate_handle():
    with BuildPart() as handle:
        # Mounting bases
        with Locations((-POST_X, 0, 0), (POST_X, 0, 0)):
            Cylinder(
                radius=BASE_RADIUS,
                height=BASE_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Vertical posts
        with Locations((-POST_X, 0, BASE_HEIGHT), (POST_X, 0, BASE_HEIGHT)):
            Cylinder(
                radius=POST_RADIUS,
                height=POST_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Horizontal grip
        with Locations((0, 0, GRIP_Z)):
            Cylinder(
                radius=GRIP_RADIUS,
                height=GRIP_LENGTH,
                rotation=(0, 90, 0),
            )

        # Counterbored mounting holes, drilled from the top of each base
        for x in (-POST_X, POST_X):
            for y in (-SCREW_Y, SCREW_Y):
                with Locations((x, y, BASE_HEIGHT)):
                    CounterBoreHole(
                        radius=SCREW_HOLE_RADIUS,
                        counter_bore_radius=COUNTERBORE_RADIUS,
                        counter_bore_depth=COUNTERBORE_DEPTH,
                    )

        # Round the exposed grip ends
        grip_end_edges = handle.edges().filter_by(GeomType.CIRCLE).filter_by_position(
            Axis.X, -GRIP_LENGTH / 2 - 0.1, -GRIP_LENGTH / 2 + 0.1
        ) + handle.edges().filter_by(GeomType.CIRCLE).filter_by_position(
            Axis.X, GRIP_LENGTH / 2 - 0.1, GRIP_LENGTH / 2 + 0.1
        )
        fillet(grip_end_edges, radius=GRIP_END_FILLET)

    return handle


if __name__ == "__main__":
    part = generate_handle()
    export_step(part.part, "exports/handle.step")
    print("Handle compiled and exported to exports/handle.step")
    print(f"Volume: {part.part.volume:.2f} mm^3")
