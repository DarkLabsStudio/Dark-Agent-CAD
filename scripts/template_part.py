from build123d import *

def generate_bracket():
    with BuildPart() as obj:
        Box(100, 50, 10)
        fillet(obj.edges().filter_by(Axis.Z), radius=5)
        with BuildSketch(obj.faces().sort_by(Axis.Z)[-1]) as s:
            Circle(12)
        extrude(amount=4)
        with Locations(obj.faces().sort_by(Axis.Z)[-1]):
            CounterBoreHole(radius=6, counter_bore_radius=10, counter_bore_depth=4)
    return obj

if __name__ == "__main__":
    part = generate_bracket()
    export_step(part.part, "exports/generated_bracket.step")
    print("✅ Reference geometry compiled and exported successfully.")
