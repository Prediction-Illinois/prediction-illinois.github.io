"""Build every Prediction@Illinois brand asset from one ring geometry.

The mark is a probability ring: a 62% brand-orange arc and a 38% blue arc,
split by two flat-cut gaps, rotated so the orange arc rises from the lower
left, with a solid dot in the centre. The logo lockup sets the ring in place
of the "@" in Prediction@Illinois; running text keeps the "@".

Run from the repo root:  python3 brand/src/build.py
Needs rsvg-convert (SVG -> PNG), Google Chrome (HTML -> PNG, for the Manrope
lockups) and Pillow.
"""
import math
import pathlib
import subprocess
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "brand"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INK, WHITE = "#0B0D10", "#F2F4F7"
ORANGE, ORANGE_LIGHT = "#FF6B2C", "#E85D1F"   # site --brand, dark and light themes
REST_DARK = REST_LIGHT = "#3262FF"               # the 38% arc: blue, so the ring carries Illinois orange + blue

C = 2 * math.pi * 34
SPLIT = 0.62

# stroke width, gap, dot radius — thicker as the mark gets smaller
LARGE = (11, 7, 10)    # avatars, 512px mark
BOLD = (15, 10, 13)    # favicon, footer, anything under ~64px
INLINE = (17, 10, 14)  # the ring set inside the lockup at text size


def ring(geom, orange, rest, rest_opacity=1.0):
    sw, gap, dot = geom
    o, g = SPLIT * C - gap, (1 - SPLIT) * C - gap
    op = f' stroke-opacity="{rest_opacity}"' if rest_opacity < 1 else ""
    return (
        f'<g fill="none" stroke-width="{sw}" transform="rotate(135 50 50)">'
        f'<circle cx="50" cy="50" r="34" stroke="{orange}" stroke-dasharray="{o:.2f} {C:.2f}" stroke-dashoffset="{-gap / 2:.2f}"/>'
        f'<circle cx="50" cy="50" r="34" stroke="{rest}"{op} stroke-dasharray="{g:.2f} {C:.2f}" stroke-dashoffset="{-(SPLIT * C + gap / 2):.2f}"/>'
        f'</g><circle cx="50" cy="50" r="{dot}" fill="{orange}"/>'
    )


def svg(inner, bg=None, rx=0, scale=1.0):
    body = inner if scale == 1 else f'<g transform="translate(50 50) scale({scale}) translate(-50 -50)">{inner}</g>'
    back = f'<rect width="100" height="100" rx="{rx}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">{back}{body}</svg>\n'


def write(name, text):
    (OUT / name).write_text(text)


def png(svg_name, png_name, size):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(OUT / png_name), str(OUT / svg_name)], check=True)


def chrome(html, png_name, w, h, transparent=False):
    """Render HTML at 2x and downsample, so text and curves stay crisp."""
    with tempfile.TemporaryDirectory() as tmp:
        page, shot = pathlib.Path(tmp, "p.html"), pathlib.Path(tmp, "p.png")
        page.write_text(html)
        args = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                f"--window-size={w},{h}", "--virtual-time-budget=8000", f"--screenshot={shot}", page.as_uri()]
        if transparent:
            args.insert(2, "--default-background-color=00000000")
        subprocess.run(args, check=True, capture_output=True)
        Image.open(shot).resize((w, h), Image.LANCZOS).save(OUT / png_name, optimize=True)


def inline_ring(orange, rest):
    return f'<svg class="at" viewBox="0 0 100 100">{ring(INLINE, orange, rest)}</svg>'


HEAD = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@800&family=JetBrains+Mono:wght@500&display=block">
<style>
html,body{margin:0;height:100%}
body{font-family:Manrope,sans-serif;-webkit-font-smoothing:antialiased}
.wm{font-weight:800;letter-spacing:-.03em;white-space:nowrap;line-height:1}
.wm .at{display:inline-block;width:.9em;height:.9em;vertical-align:-.1em;margin:0 .025em}
.mono{font-family:'JetBrains Mono',monospace;font-weight:500;text-transform:uppercase}
.grid{position:absolute;inset:0;background-image:linear-gradient(#ffffff08 1px,transparent 1px),linear-gradient(90deg,#ffffff08 1px,transparent 1px)}
</style></head><body>"""


def main():
    old = OUT / "v2_old"   # the "@" mark set, kept once before the first ring build
    if not old.exists():
        old.mkdir()
        for f in OUT.iterdir():
            if f.is_file() and f.suffix in (".svg", ".png"):
                (old / f.name).write_bytes(f.read_bytes())

    # vector marks
    write("mark.svg", svg(ring(LARGE, ORANGE, REST_DARK)))               # for dark grounds
    write("mark-light.svg", svg(ring(LARGE, ORANGE_LIGHT, REST_LIGHT)))  # for light grounds
    write("mark-orange.svg", svg(ring(LARGE, ORANGE, ORANGE, .3)))       # one colour, any ground
    write("mark-white.svg", svg(ring(LARGE, WHITE, WHITE, .3)))
    write("mark-dark.svg", svg(ring(LARGE, INK, INK, .28)))
    write("avatar-dark.svg", svg(ring(LARGE, ORANGE, REST_DARK), bg=INK, scale=.62))
    write("avatar-orange.svg", svg(ring(LARGE, INK, INK, .3), bg=ORANGE, scale=.62))
    write("favicon.svg", svg(ring(BOLD, ORANGE, REST_DARK), bg=INK, rx=22, scale=.8))

    # rasters
    png("mark-orange.svg", "mark-orange-512.png", 512)
    png("avatar-dark.svg", "logo-400.png", 400)
    png("avatar-dark.svg", "logo-linkedin-300.png", 300)
    png("avatar-orange.svg", "logo-orange-400.png", 400)
    png("favicon.svg", "favicon-64.png", 64)
    png("favicon.svg", "apple-touch-icon-180.png", 180)

    # lockups — the ring stands in for the "@"
    for name, fg, orange, rest, tag in (("wordmark-dark.png", WHITE, ORANGE, REST_DARK, "#8A919C"),
                                        ("wordmark-light.png", INK, ORANGE_LIGHT, REST_LIGHT, "#5B6370")):
        chrome(HEAD + f"""<div style="padding:10px 14px 0;color:{fg}">
<div class="wm" style="font-size:112px">Prediction{inline_ring(orange, rest)}Illinois</div>
<div class="mono" style="font-size:21px;letter-spacing:.32em;color:{tag};margin:18px 0 0 6px">Prediction market research · UIUC</div></div>""",
               name, 1282, 180, transparent=True)

    chips = "".join(f'<span style="border:1px solid #2A2F37;border-radius:999px;padding:12px 18px;background:#11141A">{m}</span>'
                    for m in ("Elections", "Sports", "Crypto", "Economics", "Tech", "Weather"))
    chrome(HEAD + f"""<div style="position:relative;width:1200px;height:630px;background:{INK};color:{WHITE};overflow:hidden">
<div class="grid" style="background-size:150px 126px"></div>
<div style="position:absolute;left:80px;top:76px;display:flex;align-items:baseline;gap:14px">
<div class="wm" style="font-size:34px">Prediction{inline_ring(ORANGE, REST_DARK)}Illinois</div><div class="mono" style="font-size:15px;letter-spacing:.2em;color:#8A919C">· UIUC</div></div>
<div class="wm" style="position:absolute;left:80px;top:250px;font-size:82px;letter-spacing:-.035em;line-height:1.02">Prediction markets,<br><span style="color:#8A919C">traded on research.</span></div>
<div class="mono" style="position:absolute;right:80px;top:250px;display:grid;grid-template-columns:repeat(2,auto);gap:12px;font-size:13px;letter-spacing:.14em;color:#C5CBD5">{chips}</div>
<div class="mono" style="position:absolute;left:80px;bottom:72px;font-size:15px;letter-spacing:.16em;color:{ORANGE}">Fall 2026 applications open</div>
<div class="mono" style="position:absolute;right:80px;bottom:72px;font-size:14px;letter-spacing:.04em;color:#8A919C;text-transform:none">prediction-illinois.github.io</div></div>""",
           "og-image-1200x630.png", 1200, 630)

    chrome(HEAD + f"""<div style="position:relative;width:1128px;height:191px;background:{INK};color:{WHITE};overflow:hidden">
<div class="grid" style="background-size:141px 64px"></div>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px">
<div class="wm" style="font-size:52px">Prediction{inline_ring(ORANGE, REST_DARK)}Illinois</div>
<div class="mono" style="font-size:12.5px;letter-spacing:.3em;color:#8A919C">Prediction market research · UIUC</div></div></div>""",
           "linkedin-cover-1128x191.png", 1128, 191)
    print("built", sorted(p.name for p in OUT.iterdir() if p.is_file()))


if __name__ == "__main__":
    main()
