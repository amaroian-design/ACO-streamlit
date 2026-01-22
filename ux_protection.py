# ux_protection.py
# -------------------------------------------------
# CONTROLES DE EXPOSICIÓN UX
# -------------------------------------------------

def get_exposure_level(run_count: int) -> str:
    """
    Controla cuánta información se muestra según uso.
    """
    if run_count <= 2:
        return "full"
    elif run_count <= 5:
        return "reduced"
    else:
        return "minimal"


def classify_activity(x: float) -> str:
    """
    Clasificación semántica (no numérica).
    """
    if x < 0.05:
        return "Low"
    elif x < 0.15:
        return "Moderate"
    elif x < 0.35:
        return "High"
    else:
        return "Critical"


def structural_label(num_changes: int, total_steps: int) -> str:
    """
    Sustituye métricas exactas por lenguaje ejecutivo.
    """
    ratio = num_changes / max(total_steps, 1)

    if ratio < 0.1:
        return "Structurally Stable"
    elif ratio < 0.25:
        return "Elevated Adaptation"
    else:
        return "Structurally Unstable"
