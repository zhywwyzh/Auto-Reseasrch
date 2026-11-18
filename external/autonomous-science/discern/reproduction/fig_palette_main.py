"""Soft blue--coral palette for main Figures 2--5 only.
Author-selected option B, inspired by AlphaFold 3 (Nature 2024), Figure 2d.
Adaptations, not an official Nature palette. Figure 1 and appendix assets stay unchanged.
"""
BLUE, NAVY, LIGHT_BLUE = '#3579B1', '#2F668F', '#A8CCDF'
ORANGE, LIGHT_ORANGE, PALE_ORANGE, BROWN = '#D86858', '#F0AA9A', '#F8D6CC', '#AF484C'
GREEN, MID_GREEN, LIGHT_GREEN = '#469E96', '#66B8AD', '#CEE8E4'
RED, LIGHT_RED = '#B93C60', '#DF5462'
PURPLE, LIGHT_PURPLE = '#7389B5', '#B7C5DF'
GREY = '#A7ADB3'

# Teal = complete; coral tints = partial; raspberry = failure; periwinkle = abstention.
OUTCOME = {
    'DIAGNOSE-AND-ACT': MID_GREEN, 'DIAGNOSE-AND-ACT-PARTIAL': '#ED7B62', 'DIAGNOSE-NOT-ACT': LIGHT_ORANGE,
    'NOTICE-WRONG': PALE_ORANGE, 'ABSTAIN-RECOGNIZED': PURPLE, 'ABSTAIN-OK': LIGHT_PURPLE,
    'OVER-DIAGNOSE': LIGHT_RED, 'MISS': RED, 'NONCOMPLIANT': GREY,
    'CLEAN-CORRECT': MID_GREEN, 'OVER-CAUTIOUS': LIGHT_ORANGE, 'FALSE-UNUSABLE': RED,
}
# L3 response to the stated prior (Figure 4 D)
FILL = {'data': MID_GREEN, 'mixed': '#ED7B62', 'prior': RED, 'declined': PURPLE}
# Difficulty bands (Figure 5 A)
BANDS = [('easy', MID_GREEN), ('medium', '#ED7B62'), ('hard', RED)]
# Model key (Figures 4 C, 5 A-B); retain marker shapes as a second identifier.
MODEL = {
    'gpt-5.6-sol': BLUE, 'claude-opus-5': '#ED7B62', 'kimi-k3': MID_GREEN, 'glm-5.2': '#619FB4',
    'deepseek-v4-pro': LIGHT_RED, 'gpt-4.1': GREY, 'glm-5.3': RED, 'gpt-6-astra': PURPLE,
}
STAGE = {'L1': BLUE, 'L2': ORANGE, 'L3': GREEN}
CLASS_RAMP = {
    'L1': {'clean control': '#DFEDF5', 'challenge': BLUE},
    'L2': {'clean control': '#FBEAE5', 'statistical trap': LIGHT_ORANGE,
           'tool / procedure trap': ORANGE, 'data confound': BROWN},
    'L3': {'real control': LIGHT_GREEN, 'native counterfactual': MID_GREEN,
           'injected counterfactual': GREEN},
}
QUALITY_RAMP = ['#F4F8FB', '#A8CCDF', NAVY]
# Second identifier for the model key: marker shapes (colours alone separate the greens poorly at small sizes)
MARKER = {'gpt-5.6-sol': 'o', 'claude-opus-5': 's', 'kimi-k3': '^', 'glm-5.2': 'D',
          'deepseek-v4-pro': 'v', 'gpt-4.1': 'o', 'glm-5.3': 'P', 'gpt-6-astra': 'X'}


def text_on(background):
    """Choose dark or white text by relative luminance (no size/layout change)."""
    from matplotlib.colors import to_rgb
    def luminance(color):
        channels = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4
                    for x in to_rgb(color)]
        return sum(x * w for x, w in zip(channels, [.2126, .7152, .0722]))
    lum = luminance(background)
    dark = '#202B36'
    return 'white' if 1.05 / (lum + .05) > (lum + .05) / (luminance(dark) + .05) else dark
