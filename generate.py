"""
@mindoverwant post generator.

Usage:
  python3 generate.py <week_json> <out_dir>

week_json: a JSON list of 7 objects:
  {"slug": "1_friday", "day": "FRIDAY", "quote": "...", "highlight": "phrase from the quote"}
Writes 1080x1350 JPGs (Instagram portrait) to out_dir, one per object, named <slug>.jpg.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
BG, INK, GOLD, DIM = (14, 14, 16), (245, 241, 232), (212, 168, 75), (120, 116, 108)
SUB, LINE = (185, 179, 166), (58, 53, 43)
HANDLE = "@mindoverwant"


def mark(size):
    """MW monogram in a gold ring (logo #1, small)."""
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    k = size / 1080
    c = size / 2
    r1 = 380 * k
    d.ellipse([c - r1, c - r1, c + r1, c + r1], outline=GOLD, width=max(2, int(10 * k)))
    f = ImageFont.truetype(SERIF, int(250 * k))
    wm = f.getlength("M")
    ov = int(22 * k)
    tot = wm + f.getlength("W") - ov
    x = c - tot / 2
    y = c - 160 * k
    d.text((x, y), "M", font=f, fill=INK)
    d.text((x + wm - ov, y), "W", font=f, fill=GOLD)
    return img


def wrap(text, font, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def render(post, path, small_mark):
    day, quote, hl = post["day"], post["quote"], post.get("highlight", "")
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W - 40, H - 40], outline=(40, 38, 34), width=3)
    f_day = ImageFont.truetype(SANS, 40)
    label = f"— {day.upper()} —"
    d.text(((W - f_day.getlength(label)) / 2, 150), label, font=f_day, fill=GOLD)
    d.text((110, 220), "“", font=ImageFont.truetype(SERIF, 220), fill=GOLD)
    size = 78
    while True:
        f = ImageFont.truetype(SERIF, size)
        lines = wrap(quote, f, W - 240)
        lh = int(size * 1.32)
        if len(lines) * lh < 640 or size < 48:
            break
        size -= 4
    y = 470 + (640 - len(lines) * lh) / 2
    hs = quote.lower().find(hl.lower()) if hl else -1
    pos = 0
    for line in lines:
        x = 120
        for w in line.split():
            idx = quote.find(w, pos)
            pos = idx + len(w)
            gold = hs != -1 and hs <= idx < hs + len(hl)
            d.text((x, y), w, font=f, fill=GOLD if gold else INK)
            x += f.getlength(w + " ")
        y += lh
    d.line([W / 2 - 60, H - 230, W / 2 + 60, H - 230], fill=GOLD, width=4)
    f_h = ImageFont.truetype(SANS, 42)
    tw = f_h.getlength(HANDLE)
    x0 = (W - (120 + 20 + tw)) / 2
    img.paste(small_mark, (int(x0), H - 210))
    d.text((x0 + 140, H - 175), HANDLE, font=f_h, fill=DIM)
    img.save(path, quality=90)


def main():
    week = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    m = mark(120)
    for p in week:
        render(p, os.path.join(out, p["slug"] + ".jpg"), m)
    print(f"rendered {len(week)} posts to {out}")


if __name__ == "__main__":
    main()
