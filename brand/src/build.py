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


def cover_art(png_name, w, h, paths=240, heroes=6, steps=170, seed=11, t_end=0.975):
    """LinkedIn banner without text: price paths of binary contracts.

    Each contract lists at its own price and follows p_t = Phi(W_t / sqrt(T - t)), the price
    of a claim paying 1 if Brownian motion ends above zero, so approaching expiry every path is
    pushed toward 1 or 0. Most paths form a faint silver texture; a dozen carry the colour —
    orange for those resolving Yes, blue for No — with a soft glow, over a dark ground lit warm
    at the top right and cool at the bottom right. The picture stops just short of expiry.
    """
    import numpy as np
    from statistics import NormalDist
    from PIL import ImageChops, ImageFilter
    W, H = w * 2, h * 2
    rng = np.random.default_rng(seed)
    t = np.linspace(0, t_end, steps + 1)
    listed = np.array([NormalDist().inv_cdf(q) for q in rng.uniform(.12, .88, paths)])
    walk = listed[:, None] + np.concatenate([np.zeros((paths, 1)), np.cumsum(rng.normal(0, math.sqrt(t_end / steps), (paths, steps)), axis=1)], axis=1)
    price = 0.5 * (1 + np.frompyfunc(math.erf, 1, 1)(walk / np.sqrt(2 * (1 - t))).astype(float))
    xs, ys, end = t / t_end * W, 0.1 * H + (1 - price) * 0.8 * H, walk[:, -1]

    def pick(idx):  # heroes spread from near-coin-flips to decisive resolutions
        return idx[np.argsort(np.abs(end[idx]))][np.linspace(len(idx) * .15, len(idx) - 1, heroes).astype(int)]
    hero = set(pick(np.where(end > 0)[0])) | set(pick(np.where(end <= 0)[0]))

    def smooth(y):  # quadratic curves through midpoints, so each path reads as one strand
        d = f"M{xs[0]:.1f},{y[0]:.1f}"
        for i in range(1, len(xs) - 1):
            d += f" Q{xs[i]:.1f},{y[i]:.1f} {(xs[i] + xs[i + 1]) / 2:.1f},{(y[i] + y[i + 1]) / 2:.1f}"
        return d + f" L{xs[-1]:.1f},{y[-1]:.1f}"

    def layer(items):
        body = "".join(f'<path d="{d}" fill="none" stroke="rgb{c}" stroke-opacity="{o}" stroke-width="{sw}"/>' for d, c, o, sw in items)
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = pathlib.Path(tmp, "l.svg"), pathlib.Path(tmp, "l.png")
            src.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><g style="mix-blend-mode:screen">{body}</g></svg>')
            subprocess.run(["rsvg-convert", "-o", str(dst), str(src)], check=True)
            return Image.open(dst).convert("RGBA")

    def glow(under, lines, radius, gain):
        blurred = lines.filter(ImageFilter.GaussianBlur(radius))
        lit = Image.alpha_composite(Image.new("RGBA", under.size, (0, 0, 0, 255)), blurred).convert("RGB")
        return ImageChops.screen(under, lit.point(lambda v: min(255, int(v * gain))))

    y, x = np.mgrid[0:H, 0:W].astype(float)
    ground = np.ones((H, W, 3)) * np.array((7, 9, 13), float)
    for cx, cy, sx, sy, colour in ((.82, .15, .35, .9, (60, 26, 10)), (.82, .88, .35, .9, (14, 26, 70)), (.55, .5, .5, 1.2, (12, 16, 26))):
        ground += np.exp(-(((x - cx * W) / (sx * W)) ** 2 + ((y - cy * H) / (sy * H)) ** 2))[..., None] * np.array(colour, float)
    ground = Image.fromarray(np.clip(ground, 0, 255).astype(np.uint8), "RGB")

    faint = layer([(smooth(ys[i]), (200, 208, 220), .06, 1.3) for i in range(paths) if i not in hero])
    bright = layer([(smooth(ys[i]), (255, 107, 44) if end[i] > 0 else (79, 123, 255), .9, 2.8) for i in range(paths) if i in hero])
    out = glow(glow(ground, faint, 5.4, 1.08), bright, 9, 1.8)
    out = Image.alpha_composite(Image.alpha_composite(out.convert("RGBA"), faint), bright)
    out.convert("RGB").resize((w, h), Image.LANCZOS).save(OUT / png_name, optimize=True)


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
    # text-free cover and a light logo tile: the page name already sits under the banner,
    # and a white tile reads cleanly where LinkedIn overlaps it on the dark cover
    cover_art("linkedin-cover-art-1128x191.png", 1128, 191)
    write("avatar-light.svg", svg(ring(LARGE, ORANGE_LIGHT, REST_LIGHT), bg="#FFFFFF", scale=.62))
    png("avatar-light.svg", "logo-light-400.png", 400)
    png("avatar-light.svg", "logo-linkedin-light-300.png", 300)
    print("built", sorted(p.name for p in OUT.iterdir() if p.is_file()))


if __name__ == "__main__":
    main()
