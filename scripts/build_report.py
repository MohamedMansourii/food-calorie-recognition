"""Assemble the mentor-facing delivery PDF from the project docs.

Combines: cover + FRD deliverables mapping + decision note + accuracy report
+ Tunisian model report + learning report + limitations, styled for print.
Output: delivery/Final-Report.pdf and delivery/Demo-Script.pdf (via Edge).

Run:  <venv>/python scripts/build_report.py
"""
import os
import subprocess

import markdown

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "delivery")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1e293b; font-size: 10.5pt;
       line-height: 1.55; margin: 0; }
h1 { font-size: 20pt; color: #0f172a; margin: 0 0 4px; }
h2 { font-size: 14pt; color: #047857; border-bottom: 2px solid #d1fae5;
     padding-bottom: 4px; margin-top: 28px; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #0f172a; margin-top: 18px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th { background: #ecfdf5; color: #065f46; text-align: left; }
th, td { border: 1px solid #e2e8f0; padding: 5px 8px; }
code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
a { color: #047857; }
.cover { text-align: center; padding-top: 90px; page-break-after: always; }
.cover .logo { font-size: 52pt; }
.cover h1 { font-size: 26pt; margin-top: 10px; }
.cover .sub { color: #475569; font-size: 12pt; margin-top: 6px; }
.cover .links { margin-top: 40px; font-size: 10.5pt; line-height: 2; }
.cover .meta { margin-top: 50px; color: #64748b; font-size: 10pt; }
.badge { display: inline-block; background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;
         border-radius: 12px; padding: 2px 10px; font-size: 9pt; margin: 2px; }
.section { page-break-before: always; }
blockquote { border-left: 3px solid #a7f3d0; margin: 8px 0; padding: 2px 12px; color: #475569; }
"""

COVER = """
<div class="cover">
  <div class="logo">🍽️</div>
  <h1>AI Food &amp; Calories Recognition</h1>
  <div class="sub">Internship Project — Final Delivery Report</div>
  <div style="margin-top:14px">
    <span class="badge">ViT · Food-101 · 101 dishes</span>
    <span class="badge">Own fine-tuned Tunisian model · 19 dishes</span>
    <span class="badge">Live web app · free-tier deployment</span>
  </div>
  <div class="links">
    <b>Live app:</b> <a href="https://food-calorie-recognition.netlify.app">food-calorie-recognition.netlify.app</a><br>
    <b>Source code:</b> <a href="https://github.com/MohamedMansourii/food-calorie-recognition">github.com/MohamedMansourii/food-calorie-recognition</a><br>
    <b>Model endpoint:</b> <a href="https://huggingface.co/spaces/mansourismatic/food-calorie-recognition">HF Space: mansourismatic/food-calorie-recognition</a><br>
    <b>Trained model:</b> <a href="https://huggingface.co/mansourismatic/tunisian-food-classifier">HF: mansourismatic/tunisian-food-classifier</a>
  </div>
  <div class="meta">Mohamed Mansouri · Astrolab Group internship<br>
  Mentor: Mohamed Hedi Al Mokni · August 2026</div>
</div>
"""

CHECKLIST = """
## FRD deliverables — status

| FRD deliverable (§10) | Status | Where |
|---|---|---|
| Technical approach note (comparison + recommendation) | ✅ Done | Section 2 of this report |
| Working recognition pipeline + observed accuracy notes | ✅ Done — measured, not estimated | Sections 3–4 |
| End-to-end web app (upload → recognition → calories) | ✅ Done — **live** | food-calorie-recognition.netlify.app |
| Source code in a shared repository with README | ✅ Done | GitHub repo above |
| Short learning report | ✅ Done | Section 5 |
| Final demo walkthrough (5–10 min) | ✅ Prepared — ready to present | docs/demo-script.md (rehearsed script) |

**Functional requirements:** all Must (FR-01/03/06/08) and Should (FR-02/05/07) items are implemented,
plus the Could items FR-04 (top-3 alternatives) and FR-09 (session history). FR-10/11/12 were
consciously de-scoped per the FRD's MoSCoW guidance and are listed as future work.

**Beyond the FRD:** a second recognition engine for Tunisian dishes (couscous, ojja, mloukhiya,
brik, lablabi…) was fine-tuned on three public CC-BY-4.0 datasets and deployed — Section 4.
"""


def md_file(path, drop_title=True):
    text = open(os.path.join(REPO, path), encoding="utf-8").read()
    if drop_title and text.startswith("#"):
        text = text.split("\n", 1)[1]
    return markdown.markdown(text, extensions=["tables"])


def build(html_body, out_pdf):
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html_body}</body></html>"
    tmp = os.path.join(OUT, os.path.basename(out_pdf).replace(".pdf", ".html"))
    open(tmp, "w", encoding="utf-8").write(html)
    subprocess.run([EDGE, "--headless", "--disable-gpu", f"--print-to-pdf={out_pdf}",
                    "--no-pdf-header-footer", f"file:///{tmp}"], timeout=90, check=False)
    ok = os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 10000
    print(("OK " if ok else "FAIL ") + out_pdf, os.path.getsize(out_pdf) if os.path.exists(out_pdf) else 0)
    os.remove(tmp)
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    md = markdown.markdown

    body = COVER
    body += md(CHECKLIST, extensions=["tables"])
    body += "<div class='section'><h2>1 · Project overview</h2>"
    body += md_file("README.md")  # includes how-it-works, accuracy, limitations, attribution
    body += "</div><div class='section'><h2>2 · Technical approach — decision note (Week-1 gate)</h2>"
    body += md_file("docs/decision-note.md")
    body += "</div><div class='section'><h2>3 · Measured accuracy — Food-101 engine</h2>"
    body += md_file("docs/accuracy-report.md")
    body += "</div><div class='section'><h2>4 · Tunisian dish engine — fine-tuning report</h2>"
    body += md_file("docs/tunisian-model-report.md")
    body += "</div><div class='section'><h2>5 · Learning report</h2>"
    body += md_file("docs/learning-report.md")
    body += "</div>"
    ok1 = build(body, os.path.join(OUT, "Final-Report.pdf"))

    demo = "<h1>Demo walkthrough — 8 minutes</h1>" + md_file("docs/demo-script.md")
    ok2 = build(demo, os.path.join(OUT, "Demo-Script.pdf"))
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
