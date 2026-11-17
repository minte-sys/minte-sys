"""Builds the featured-project cards: card_<slug>_dark.svg and card_<slug>_light.svg.

Edit PROJECTS below and run:  python make_cards.py
The links live in README.md; these files are just the pictures.
"""
import textwrap
from xml.sax.saxutils import escape

W, H = 420, 270
FONT = "ConsolasFallback,Consolas,'DejaVu Sans Mono',Menlo,monospace"

THEMES = {
    "dark": dict(bg="#161b22", bar="#0d1117", border="#30363d", text="#c9d1d9", dim="#8b949e",
                 key="#ffa657", value="#a5d6ff", good="#3fb950", chip="#1f2a37"),
    "light": dict(bg="#f6f8fa", bar="#eaeef2", border="#d0d7de", text="#24292f", dim="#57606a",
                  key="#953800", value="#0a3069", good="#1a7f37", chip="#ddf4ff"),
}

PROJECTS = [
    dict(slug="clinic", repo="clinic-voice-agent", name="Clinic Voice Agent",
         desc="Books, reschedules and cancels clinic appointments by voice or by text chat.",
         highlight="EN · AR · HI · ZH · RU",
         tags=["Python", "LiveKit", "SQLite"]),
    dict(slug="airwriting", repo="air-writing", name="Air-Writing",
         desc="Write in the air with a fingertip. A NumPy neural net reads the letters and "
              "learns your handwriting.",
         highlight="trained on 104k synthetic letters",
         tags=["OpenCV", "MediaPipe", "NumPy"]),
    dict(slug="triagebot", repo="TriageBot", name="TriageBot",
         desc="LLM agent that triages GitHub issues and earns autonomy one action type "
              "at a time.",
         highlight="every action audited & undoable",
         tags=["Python", "LLM agents", "Docker"]),
]


def card(p, t):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="{FONT}">',
           "<style>@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
           ".cursor{animation:blink 1.1s step-end infinite} text{white-space:pre}</style>",
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="{t["bg"]}" '
           f'stroke="{t["border"]}" stroke-width="2"/>',
           # window title bar
           f'<path d="M2 11a9 9 0 0 1 9-9h{W - 22}a9 9 0 0 1 9 9v23H2z" fill="{t["bar"]}"/>',
           f'<line x1="2" y1="34" x2="{W - 2}" y2="34" stroke="{t["border"]}" stroke-width="1.5"/>',
           '<circle cx="20" cy="18" r="5.5" fill="#ff5f57"/>',
           '<circle cx="38" cy="18" r="5.5" fill="#febc2e"/>',
           '<circle cx="56" cy="18" r="5.5" fill="#28c840"/>',
           f'<text x="{W / 2}" y="23" text-anchor="middle" font-size="13" fill="{t["dim"]}">'
           f'~/{escape(p["repo"])}</text>',
           # name
           f'<text x="22" y="70" font-size="21" font-weight="bold" fill="{t["key"]}">{escape(p["name"])}</text>']
    # description, wrapped
    for i, line in enumerate(textwrap.wrap(p["desc"], 41)[:3]):
        out.append(f'<text x="22" y="{100 + i * 21}" font-size="14.5" fill="{t["text"]}">{escape(line)}</text>')
    out.append(f'<text x="22" y="174" font-size="14" fill="{t["good"]}">+ {escape(p["highlight"])}</text>')
    # tag chips
    x = 22
    for tag in p["tags"]:
        cw = len(tag) * 7.83 + 18
        out.append(f'<rect x="{x:.1f}" y="192" width="{cw:.1f}" height="24" rx="12" fill="{t["chip"]}"/>')
        out.append(f'<text x="{x + cw / 2:.1f}" y="208.5" text-anchor="middle" font-size="13" '
                   f'fill="{t["value"]}">{escape(tag)}</text>')
        x += cw + 8
    # prompt
    out.append(f'<text x="22" y="247" font-size="14" xml:space="preserve"><tspan fill="{t["key"]}">&gt;</tspan>'
               f'<tspan fill="{t["dim"]}"> open repo</tspan></text>')
    out.append(f'<rect class="cursor" x="{22 + 12 * 8.43:.1f}" y="235" width="8.4" height="16" fill="{t["value"]}"/>')
    out.append("</svg>\n")
    return "\n".join(out)


if __name__ == "__main__":
    for p in PROJECTS:
        for mode, theme in THEMES.items():
            with open(f"card_{p['slug']}_{mode}.svg", "w", encoding="utf-8") as f:
                f.write(card(p, theme))
    print("wrote", len(PROJECTS) * 2, "cards")
