"""Shared config for the *_8models figures: the frozen six plus glm-5.3 and gpt-6-astra.

Import this INSTEAD of touching fig_common.MODEL_ORDER. Everything else (colours, ink, save,
footnote, tidy) still comes from fig_common, so an extended builder is the original with the model
list and the input table swapped:

    import fig_common as C, fig_common_ext as X
    rows = X.load("fig_data_l1_8models.csv")
    for m in X.MODELS: ...

The two later models are drawn in colours outside the frozen palette and are flagged `is_new()` so a
builder can mark them (italic label, diamond marker) without hard-coding names.
"""
import fig_common as C

NEW = ["glm-5.3", "gpt-6-astra"]
MODELS = [*C.MODEL_ORDER, *NEW]
SHORT = {**C.SHORT, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}
FULL = {**C.FULL, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}
COLOR = {**C.COLOR, "glm-5.3": "#7B4FA8", "gpt-6-astra": "#146B63"}
load = C.load


def is_new(m):
    return m in NEW


def mark_new(labels, models):
    """Italicise the tick labels of post-freeze models (used instead of a 9th legend key)."""
    for lab, m in zip(labels, models):
        if is_new(m):
            lab.set_fontstyle("italic")
