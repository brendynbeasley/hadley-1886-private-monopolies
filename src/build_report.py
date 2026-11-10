"""Assemble docs/index.html from the template, the essay and the figures."""
import html
import re

from config import DOCS, PAPER, ROOT
from make_figures import build


def essay_html():
    text = (PAPER / "essay.md").read_text()
    paras = [p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("#") and not p.startswith("*A reading")]
    out = []
    for p in paras:
        p = html.escape(p, quote=False)
        p = re.sub(r"\*(.+?)\*", r"<cite>\1</cite>", p)
        out.append(f"<p>{p}</p>")
    return "\n".join(out)


def main():
    page = (ROOT / "src" / "report_template.html").read_text()
    figs = build()
    page = page.replace("{{ESSAY}}", essay_html()).replace("{{ROWS}}", figs["rows"])
    for key in ["A1", "A2", "B", "C", "D", "E", "F"]:
        page = page.replace("{{%s}}" % key, figs[key])
    assert "{{" not in page, "unfilled placeholder"
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(page)
    (DOCS / ".nojekyll").write_text("")
    print(f"docs/index.html ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
