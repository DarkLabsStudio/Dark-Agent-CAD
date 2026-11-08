"""Liquid-cooling cold plate with an internal serpentine channel.

Geometry
--------
- Block: 120 x 80 x 20 mm
- Internal channel: 8 mm diameter, four-pass serpentine at mid-height
- Ports: two 10 mm vertical ports with 18 mm bosses, 4 mm above the block
- Mounting: four M4 clearance holes with 8 mm counterbores, 4 mm deep

The serpentine cavity is built from overlapping cylinders and subtracted from
the block. The two vertical ports connect the channel ends to the top surface,
so the finished part is a single watertight solid with an internal flow path.
"""

from build123d import *

# Block
BLOCK_X = 120.0
BLOCK_Y = 80.0
BLOCK_Z = 20.0

# Internal channel
CHANNEL_RADIUS = 4.0
CHANNEL_Z = 10.0
PASS_X = 45.0
PASS_Y = (-25.0, -8.0, 9.0, 26.0)

# Ports
PORT_RADIUS = 5.0
PORT_X = -PASS_X
PORT_Y = (PASS_Y[0], PASS_Y[-1])
BOSS_RADIUS = 9.0
BOSS_HEIGHT = 5.0
BOSS_OVERLAP = 1.0

# Mounting holes
MOUNT_X = 55.0
MOUNT_Y = 35.0
MOUNT_HOLE_RADIUS = 2.25  # M4 clearance
MOUNT_CBORE_RADIUS = 4.0
MOUNT_CBORE_DEPTH = 4.0


def generate_cooling_block():
    with BuildPart() as block:
        Box(
            BLOCK_X,
            BLOCK_Y,
            BLOCK_Z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # Port bosses on the top face
        with Locations(
            *[(PORT_X, y, BLOCK_Z - BOSS_OVERLAP) for y in PORT_Y]
        ):
            Cylinder(
                radius=BOSS_RADIUS,
                height=BOSS_HEIGHT + BOSS_OVERLAP,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Four horizontal channel passes
        for y in PASS_Y:
            with Locations((0, y, CHANNEL_Z)):
                Cylinder(
                    radius=CHANNEL_RADIUS,
                    height=2 * PASS_X,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )

        # Three vertical connectors joining the passes into a serpentine
        connector_centers = (
            (PASS_X, (PASS_Y[0] + PASS_Y[1]) / 2, PASS_Y[1] - PASS_Y[0]),
            (-PASS_X, (PASS_Y[1] + PASS_Y[2]) / 2, PASS_Y[2] - PASS_Y[1]),
            (PASS_X, (PASS_Y[2] + PASS_Y[3]) / 2, PASS_Y[3] - PASS_Y[2]),
        )
        for x, y, height in connector_centers:
            with Locations((x, y, CHANNEL_Z)):
                Cylinder(
                    radius=CHANNEL_RADIUS,
                    height=height,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )

        # Vertical inlet and outlet ports through the bosses
        for y in PORT_Y:
            with Locations((PORT_X, y, CHANNEL_Z - 2)):
                Cylinder(
                    radius=PORT_RADIUS,
                    height=(BLOCK_Z + BOSS_HEIGHT) - (CHANNEL_Z - 2),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        # Counterbored mounting holes
        for x in (-MOUNT_X, MOUNT_X):
            for y in (-MOUNT_Y, MOUNT_Y):
                with Locations((x, y, BLOCK_Z)):
                    CounterBoreHole(
                        radius=MOUNT_HOLE_RADIUS,
                        counter_bore_radius=MOUNT_CBORE_RADIUS,
                        counter_bore_depth=MOUNT_CBORE_DEPTH,
                    )

    return block


if __name__ == "__main__":
    part = generate_cooling_block()
    export_step(part.part, "exports/cooling_block.step")
    print("Cooling block compiled and exported to exports/cooling_block.step")
    print(f"Volume: {part.part.volume:.2f} mm^3")
