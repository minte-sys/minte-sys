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
    ("stats_repos",),
    ("stats_commits",),
    ("stats_loc",),
]

WIDTH = 58          # characters in the info column
FONT_SIZE = 16
ASCII_FONT = 8      # the portrait uses smaller text for more detail
ASCII_LINE = 10.8
ASCII_CHAR_W = 4.82
ASCII_TOP = 20
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

    return dict(repos=page["totalCount"], contributed=d["repositoriesContributedTo"]["totalCount"],
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
    h = int(max(TOP + (len(info_lines) - 1) * LINE_H, ASCII_TOP + (len(ascii_lines) - 1) * ASCII_LINE) + 20)

    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',Menlo,monospace" '
           f'width="{w}px" height="{h}px" font-size="{FONT_SIZE}px">',
           "<style>",
           f".key{{fill:{t['key']}}} .value{{fill:{t['value']}}} .dots{{fill:{t['dots']}}} "
           f".text{{fill:{t['text']}}} .add{{fill:{t['add']}}} .dele{{fill:{t['dele']}}}",
           "text,tspan{white-space:pre}",
           " ".join(f".s{k}{{fill-opacity:{t['shade_floor'] + (1 - t['shade_floor']) * k / 9:.2f}}}" for k in range(10)),
           "</style>",
           f'<rect width="{w}px" height="{h}px" fill="{t["bg"]}" stroke="{t["border"]}" rx="15"/>',
           f'<text x="{ASCII_X}" y="{ASCII_TOP}" class="text" font-size="{ASCII_FONT}px" xml:space="preserve">']
    for i, a in enumerate(ascii_lines):
        out.append(f'<tspan x="{ASCII_X}" y="{ASCII_TOP + i * ASCII_LINE:g}">{shade_runs(a, shades[i])}</tspan>')
    out.append("</text>")
    out.append(f'<text x="{info_x:.0f}" y="{TOP}" class="text" xml:space="preserve">')
    for i, segs in enumerate(info_lines):
        if not segs:
            continue
        body = "".join(f'<tspan class="{c}">{escape(s)}</tspan>' for s, c in segs)
        out.append(f'<tspan x="{info_x:.0f}" y="{TOP + i * LINE_H}">{body}</tspan>')
    out.append("</text>\n</svg>\n")
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
