# Reference artifacts

These files are checked-in, known-good outputs from the scripts in `scripts/`.
They are useful for inspecting the expected geometry without running the CAD
kernel first.

| File | Description |
| --- | --- |
| `bracket.step` | Reference bracket from `scripts/template_part.py` |
| `handle.step` | Pull handle from `scripts/handle.py` |
| `cooling_block.step` | Liquid-cooling cold plate from `scripts/cooling_block.py` |
| `cooling_channel.step` | Internal serpentine channel void, for inspection |
| `p_trap.step` | Hollow P-trap fitting from `scripts/p_trap.py` |
| `previews/cooling_block.png` | Shaded cooling-block preview |
| `previews/cooling_block_section.png` | Cooling block cut at Z = 10 mm |
| `previews/cooling_block_plan.png` | Top-down section through the channel |
| `previews/cooling_channel.png` | Internal channel rendered on its own |
| `previews/handle.png` | Shaded pull-handle preview |
| `previews/p_trap.png` | Shaded P-trap preview on a white background |

Regenerate the STEP files and previews with the commands in the repository
`README.md` or `setup.md`. Generated copies in `exports/` and `renders/` are
ignored by Git.
