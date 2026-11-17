"""Builds dark_mode.svg and light_mode.svg: a neofetch-style GitHub profile card.

Edit the CONFIG section below, then either:
  * push it, and let the GitHub Action rebuild the card daily with live stats, or
  * run locally:  GH_TOKEN=<token> GH_USER=<username> python build.py
    (without a token the stats show as "—")

Standard library only — no pip installs needed.
"""
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

# ───────────────────────────── CONFIG ─────────────────────────────
HANDLE = "wuky"                     # left part of the "wuky@github" title
USERNAME = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "minte-sys"
BIRTHDAY = None                     # e.g. dt.date(2003, 5, 17) + an ("uptime_or", "Status", "...") line in INFO

INFO = [
    ("kv", "OS", "Windows, Linux (learning)"),
    ("kv", "Kernel", "Computer Engineering"),
    ("kv", "IDE", "VS Code"),
    ("blank",),
    ("kv", "Languages.Programming", "Python, JavaScript, C++"),
    ("kv", "Languages.Computer", "HTML, CSS, SQL"),
    ("kv", "Languages.Real", "English, Amharic"),
    ("blank",),
    ("kv", "Projects.Voice", "Clinic Voice Agent (5 languages)"),
    ("kv", "Projects.Chat", "Support Agent, TriageBot"),
    ("kv", "Projects.Vision", "Air-Writing (hand tracking)"),
    ("kv", "Projects.Research", "Passive RF Material Sensing"),
    ("kv", "Interests.AI", "Machine Learning, AI Agents"),
    ("kv", "Interests.Dev", "Software, Computer Vision"),
    ("blank",),
    ("section", "Contact"),
    ("kv", "Email", "mintesnotmengesha55@gmail.com"),
    ("kv", "LinkedIn", "mintesnot-mengesha-b09b0b288"),
    ("kv", "GitHub", "{username}"),
    ("blank",),
    ("section", "GitHub Stats"),
    ("stats_building",),
    ("stats_repos",),
    ("stats_commits",),
    ("stats_loc",),
]

PROMPT = True       # blinking "> █" terminal cursor under the info column
BOOT = True         # play a short "boot" animation: neofetch is typed, then everything appears
WIDTH = 58          # characters in the info column
FONT_SIZE = 16
ASCII_FONT = 8      # the portrait uses smaller text for more detail
ASCII_LINE = 10.8
ASCII_CHAR_W = 4.82
LINE_H = 20
CHAR_W = 9.63       # monospace advance at 16px
ASCII_X = 15
TOP = 30

THEMES = {
    "dark_mode.svg": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                          dots="#616e7f", add="#3fb950", dele="#f85149", border="#30363d",
                          shade_floor=0.30),   # keeps dark hair visible on the dark card
    "light_mode.svg": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                           dots="#c2cfde", add="#1a7f37", dele="#cf222e", border="#d0d7de",
                           shade_floor=0.10),
}
# ──────────────────────────────────────────────────────────────────

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _req(url, body=None):
    headers = {"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-card",
               "Accept": "application/vnd.github+json"}
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else None)


def gql(query, **variables):
    _, out = _req(f"{API}/graphql", {"query": query, "variables": variables})
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def fetch_stats(login):
    repos, stars, cursor = [], 0, None
    while True:
        d = gql("""query($login:String!,$cursor:String){user(login:$login){
              createdAt followers{totalCount}
              repositoriesContributedTo(includeUserRepositories:false,
                contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}
              repositories(ownerAffiliations:OWNER,first:100,after:$cursor){
                totalCount nodes{name isFork stargazerCount}
                pageInfo{hasNextPage endCursor}}}}""", login=login, cursor=cursor)["user"]
        page = d["repositories"]
        repos += page["nodes"]
        stars += sum(n["stargazerCount"] for n in page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    # commits: contributionsCollection spans at most one year, so walk year by year
    created = dt.datetime.fromisoformat(d["createdAt"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    commits, start = 0, created
    while start < now:
        end = min(start + dt.timedelta(days=365), now)
        c = gql("""query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
                 contributionsCollection(from:$from,to:$to){totalCommitContributions}}}""",
                login=login, **{"from": start.isoformat(), "to": end.isoformat()})
        commits += c["user"]["contributionsCollection"]["totalCommitContributions"]
        start = end

    # lines of code: additions/deletions authored by you in your own (non-fork) repos
    add = dele = 0
    for repo in repos:
        if repo["isFork"]:
            continue
        for _ in range(8):  # GitHub answers 202 while it computes the stats
            try:
                status, data = _req(f"{API}/repos/{login}/{repo['name']}/stats/contributors")
            except urllib.error.HTTPError:
                status, data = 0, None
            if status != 202:
                break
            time.sleep(3)
        for c in data or []:
            if c.get("author") and c["author"]["login"].lower() == login.lower():
                add += sum(w["a"] for w in c["weeks"])
                dele += sum(w["d"] for w in c["weeks"])

    # most recently pushed public repo (not this profile repo, which the bot pushes daily)
    recent = gql("""query($login:String!){user(login:$login){
        repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:5,
                     orderBy:{field:PUSHED_AT,direction:DESC}){nodes{name pushedAt}}}}""",
                 login=login)["user"]["repositories"]["nodes"]
    building = when = None
    for r in recent:
        if r["name"].lower() != login.lower():
            building = r["name"]
            pushed = dt.datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00"))
            days = (now.date() - pushed.date()).days
            when = "today" if days <= 0 else "yesterday" if days == 1 else f"{days} days ago"
            break

    return dict(building=building, building_when=when, repos=page["totalCount"], contributed=d["repositoriesContributedTo"]["totalCount"],
                stars=stars, followers=d["followers"]["totalCount"], commits=commits,
                loc=add - dele, add=add, dele=dele)


def uptime(born):
    today = dt.date.today()
    y = today.year - born.year
    m = today.month - born.month
    d = today.day - born.day
    if d < 0:
        m -= 1
        prev = (today.replace(day=1) - dt.timedelta(days=1))
        d += prev.day
    if m < 0:
        y -= 1
        m += 12
    s = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{s(y, 'year')}, {s(m, 'month')}, {s(d, 'day')}"


# ─────────────── line layout: a line is a list of (text, css-class) ───────────────
def kv(key, value, width=WIDTH, prefix=". "):
    """'. Key: ........ value' padded to `width`. value may be a str or segments."""
    segs = value if isinstance(value, list) else [(value, "value")]
    vlen = sum(len(t) for t, _ in segs)
    ndots = max(width - len(prefix) - len(key) - 1 - vlen - 2, 1)
    return [(prefix, "dots"), (key, "key"), (":", "text"), (" " + "." * ndots + " ", "dots")] + segs


def rule(title, first):
    head = f"{first}{title} " if title else first
    return [(head, "text"), ("—" * (WIDTH - len(head)), "text")]


def layout(stats):
    fmt = lambda n: "—" if n is None else f"{n:,}"
    st = stats or {}
    lines = [rule(f"{HANDLE}@github", "")]
    for item in INFO:
        kind = item[0]
        if kind == "kv":
            lines.append(kv(item[1], item[2].format(username=USERNAME)))
        elif kind == "uptime_or":
            lines.append(kv("Uptime", uptime(BIRTHDAY)) if BIRTHDAY else kv(item[1], item[2]))
        elif kind == "blank":
            lines.append([])
        elif kind == "section":
            lines.append(rule(item[1], "- "))
        elif kind == "stats_repos":
            left = kv("Repos", [(fmt(st.get("repos")), "value"), (" {", "text"), ("Contributed: ", "key"),
                               (fmt(st.get("contributed")), "value"), ("}", "text")], width=36)
            lines.append(left + [(" | ", "text")] + kv("Stars", fmt(st.get("stars")), width=WIDTH - 39, prefix=""))
        elif kind == "stats_commits":
            left = kv("Commits", fmt(st.get("commits")), width=36)
            lines.append(left + [(" | ", "text")] + kv("Followers", fmt(st.get("followers")), width=WIDTH - 39, prefix=""))
        elif kind == "stats_building":
            name = st.get("building") or "—"
            when = st.get("building_when")
            lines.append(kv("Currently.Building", [(name, "value")] + ([(f" ({when})", "dots")] if when else [])))
        elif kind == "stats_loc":
            lines.append(kv("Lines of Code on GitHub", [
                (fmt(st.get("loc")), "value"), (" ( ", "text"),
                (fmt(st.get("add")) + "++", "add"), (", ", "text"),
                (fmt(st.get("dele")) + "--", "dele"), (" )", "text")]))
    return lines


def shade_runs(line, shade):
    """Group neighbouring characters with the same shade into one <tspan>."""
    shade = shade.ljust(len(line), "0")
    out, i = [], 0
    while i < len(line):
        j = i
        while j < len(line) and shade[j] == shade[i]:
            j += 1
        text = escape(line[i:j])
        out.append(text if line[i:j].strip() == "" else f'<tspan class="s{shade[i]}">{text}</tspan>')
        i = j
    return "".join(out)


def render(theme, ascii_lines, info_lines, shades):
    t = THEMES[theme]
    ascii_cols = max(len(a) for a in ascii_lines)
    info_x = ASCII_X + ascii_cols * ASCII_CHAR_W + 25
    w = int(info_x + WIDTH * CHAR_W + 15)
    top = TOP + (2 * LINE_H if BOOT else 0)              # room for the "$ neofetch" line
    info_rows = len(info_lines) + (2 if PROMPT else 0)
    h = int(top + (info_rows - 1) * LINE_H + 22)
    art_h = (len(ascii_lines) - 1) * ASCII_LINE
    ascii_top = (h - art_h) / 2 + 3                       # centre the portrait vertically

    # boot timeline (seconds)
    cmd = "neofetch"
    type_start, per_char = 0.4, 0.09
    type_end = type_start + len(cmd) * per_char
    art_start = type_end + 0.3
    info_start = art_start + 0.15
    per_line = 0.07
    prompt_at = info_start + len(info_lines) * per_line + 0.2
    delay = lambda s: f' class="a" style="animation-delay:{s:.2f}s"' if BOOT else ""

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',Menlo,monospace" '
           f'width="{w}px" height="{h}px" font-size="{FONT_SIZE}px">',
           "<style>",
           f".key{{fill:{t['key']}}} .value{{fill:{t['value']}}} .dots{{fill:{t['dots']}}} "
           f".text{{fill:{t['text']}}} .add{{fill:{t['add']}}} .dele{{fill:{t['dele']}}}",
           "text,tspan{white-space:pre}",
           "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}} .cursor{animation:blink 1.1s step-end infinite}",
           "@keyframes boot{from{opacity:0}to{opacity:1}} .a{animation:boot .3s ease-out backwards}",
           " ".join(f".s{k}{{fill-opacity:{t['shade_floor'] + (1 - t['shade_floor']) * k / 9:.2f}}}" for k in range(10)),
           "</style>",
           f'<rect width="{w}px" height="{h}px" fill="{t["bg"]}" stroke="{t["border"]}" rx="15"/>']

    # "user@github:~$ neofetch", typed one character at a time
    if BOOT:
        user = f"{HANDLE}@github"
        cmd_x = info_x + (len(user) + 4) * CHAR_W
        out.append(f'<text x="{info_x:.0f}" y="{TOP}"><tspan class="add">{escape(user)}</tspan>'
                   f'<tspan class="text">:</tspan><tspan class="value">~</tspan><tspan class="text">$ </tspan></text>')
        times = [0] + [type_start + k * per_char for k in range(len(cmd) + 1)]
        widths = [0] + [k * CHAR_W for k in range(len(cmd) + 1)]
        key_times = ";".join(f"{x / type_end:.4f}" for x in times)
        out.append(
            f'<clipPath id="typed"><rect x="{cmd_x:.1f}" y="{TOP - 16}" width="{len(cmd) * CHAR_W:.1f}" height="22">'
            f'<animate attributeName="width" values="{";".join(f"{x:.1f}" for x in widths)}" keyTimes="{key_times}" '
            f'dur="{type_end:.2f}s" calcMode="discrete" fill="freeze"/></rect></clipPath>')
        out.append(f'<text x="{cmd_x:.1f}" y="{TOP}" class="text" clip-path="url(#typed)">{cmd}</text>')
        # a cursor that follows the typing, then disappears
        xs = [cmd_x] + [cmd_x + k * CHAR_W for k in range(len(cmd) + 1)]
        out.append(
            f'<rect x="{cmd_x + len(cmd) * CHAR_W:.1f}" y="{TOP - 14}" width="{CHAR_W:.1f}" height="18" '
            f'fill="{t["value"]}" opacity="0">'
            f'<animate attributeName="x" values="{";".join(f"{x:.1f}" for x in xs)}" keyTimes="{key_times}" '
            f'dur="{type_end:.2f}s" calcMode="discrete" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.999;1" dur="{type_end + 0.2:.2f}s" '
            f'calcMode="discrete" fill="freeze"/></rect>')

    # portrait, revealed top to bottom like a scan
    for i, a in enumerate(ascii_lines):
        if not a.strip():
            continue
        out.append(f'<text x="{ASCII_X}" y="{ascii_top + i * ASCII_LINE:.1f}" font-size="{ASCII_FONT}px" '
                   f'xml:space="preserve"{delay(art_start + i * 0.03)}>'
                   f'<tspan class="text">{shade_runs(a, shades[i])}</tspan></text>')

    # info lines, one after another
    for i, segs in enumerate(info_lines):
        if not segs:
            continue
        body = "".join(f'<tspan class="{c}">{escape(s)}</tspan>' for s, c in segs)
        out.append(f'<text x="{info_x:.0f}" y="{top + i * LINE_H}" xml:space="preserve"'
                   f'{delay(info_start + i * per_line)}>{body}</text>')

    if PROMPT:
        py = top + (len(info_lines) + 1) * LINE_H
        out.append(f'<g{delay(prompt_at)}><text x="{info_x:.0f}" y="{py}" class="key">&gt;</text>'
                   f'<rect class="cursor" x="{info_x + 2 * CHAR_W:.0f}" y="{py - 14}" width="{CHAR_W:.1f}" '
                   f'height="18" fill="{t["value"]}"/></g>')
    out.append("</svg>\n")
    return "\n".join(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    stats = None
    if TOKEN:
        try:
            stats = fetch_stats(USERNAME)
            print("stats:", stats)
        except Exception as e:  # keep building the card even if the API hiccups
            print("could not fetch stats:", e)
    else:
        print("no GH_TOKEN set: building with placeholder stats")

    info = layout(stats)
    for name in THEMES:
        mode = "dark" if name.startswith("dark") else "light"
        with open(os.path.join(here, f"ascii_{mode}.txt"), encoding="utf-8") as f:
            ascii_lines = f.read().rstrip("\n").split("\n")
        with open(os.path.join(here, f"shade_{mode}.txt"), encoding="utf-8") as f:
            shades = f.read().rstrip("\n").split("\n")
        with open(os.path.join(here, name), "w", encoding="utf-8") as f:
            f.write(render(name, ascii_lines, info, shades))
        print("wrote", name)


if __name__ == "__main__":
    main()
