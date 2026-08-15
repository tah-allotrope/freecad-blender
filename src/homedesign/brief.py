"""Brief-copy scaffolding (PHASE-06): generate the hand-authored brief JSON."""
from __future__ import annotations

from .model import CompiledModel


def scaffold_brief(model: CompiledModel) -> dict:
    """A brief-copy dictionary derived from the compiled model, ready for a
    human to fill in the narrative and requirements."""
    total_gfa = sum(
        (r.rect.w / 1000) * (r.rect.d / 1000) for s in model.storeys for r in s.rooms
    )
    plot_w = model.plot_width_mm / 1000
    plot_d = model.plot_depth_mm / 1000
    title = model.name.replace("-", " ").replace("_", " ").title()
    subtitle = (
        f"{len(model.storeys)} storeys, {total_gfa:.0f} m² on a "
        f"{plot_w:.2f} × {plot_d:.2f} m plot"
    )
    return {
        "title": title,
        "subtitle": subtitle,
        "narrative": ["(placeholder — write the design intent here)"],
        "requirements": [
            "(placeholder — confirm programme)",
            "(placeholder — confirm materials)",
            "(placeholder — confirm delivery format)",
        ],
    }
