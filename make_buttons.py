"""Builds the terminal-style link buttons shown under the profile card.

Run once (python make_buttons.py) -> writes btn_<name>_dark.svg and _light.svg.
The links themselves live in README.md; these are just the pictures.
"""
import os

W, H = 320, 64
THEMES = {
    "dark": dict(bg="#161b22", border="#30363d", text="#c9d1d9"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", text="#24292f"),
}

# icon drawings, 30x30, drawn at (0,0); `c` is the accent colour
ICONS = {
    "projects": lambda c: (
        f'<path d="M2 7h10l3 3h13v16H2z" fill="none" stroke="{c}" stroke-width="2.4" stroke-linejoin="round"/>'
        f'<path d="M9 16l-3 3 3 3M21 16l3 3-3 3M17 15l-4 9" fill="none" stroke="{c}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'),
    "linkedin": lambda c, ink=None: (
        f'<rect x="1" y="1" width="28" height="28" rx="4" fill="{c}"/>'
        f'<rect x="6.5" y="12" width="4" height="12" fill="{INK[c]}"/>'
        f'<circle cx="8.5" cy="7.8" r="2.4" fill="{INK[c]}"/>'
        f'<path d="M13.5 12h3.8v1.8c.7-1.2 2-2.1 4-2.1 3 0 4.2 1.9 4.2 5.2V24h-4v-6.3c0-1.6-.5-2.6-1.9-2.6'
        f'-1.5 0-2.1 1.1-2.1 2.6V24h-4z" fill="{INK[c]}"/>'),
    "email": lambda c: (
        f'<rect x="2" y="5" width="26" height="20" rx="2" fill="none" stroke="{c}" stroke-width="2.4"/>'
        f'<path d="M3 7l12 9 12-9" fill="none" stroke="{c}" stroke-width="2.4" stroke-linejoin="round"/>'),
}

INK = {"#a5d6ff": "#0d1117", "#0a66c2": "#ffffff"}  # colour of the "in" letters

BUTTONS = [  # (file name, label, accent colour dark, accent colour light)
    ("projects", "PROJECTS", "#ffa657", "#bc4c00"),
    ("linkedin", "LINKEDIN", "#a5d6ff", "#0a66c2"),
    ("email", "EMAIL", "#ff7b72", "#cf222e"),
]


def button(name, label, accent, t):
    char_w = 18 * 0.6
    label_w = len(label) * char_w + (len(label) - 1) * 1.5
    group_w = 30 + 14 + label_w
    x0 = (W - group_w) / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="6" fill="{t['bg']}" stroke="{t['border']}" stroke-width="2"/>
<rect x="6" y="{H - 8}" width="{W - 12}" height="4" rx="1" fill="{accent}"/>
<g transform="translate({x0:.1f},15)">{ICONS[name](accent)}</g>
<text x="{x0 + 44:.1f}" y="38" fill="{t['text']}" font-size="18" letter-spacing="1.5"
 font-family="ConsolasFallback,Consolas,'DejaVu Sans Mono',Menlo,monospace">{label}</text>
</svg>
'''


if __name__ == "__main__":
    pass
    for name, label, dark, light in BUTTONS:
        for mode, accent in (("dark", dark), ("light", light)):
            with open(f"btn_{name}_{mode}.svg", "w", encoding="utf-8") as f:
                f.write(button(name, label, accent, THEMES[mode]))
    print("wrote", len(BUTTONS) * 2, "buttons")
