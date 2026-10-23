"""
@mindoverwant motivational Reel generator (9:16, ~11 s, original music).

Usage:
  python3 reel.py <reel_json> <out_mp4>

reel_json: {"hook": "Read this if you feel like quitting.",
            "lines": ["Discipline is", "remembering what you want", "more than what you want", "right now."],
            "gold": [2]}          # indexes of lines shown in gold (optional)
Structure: 0-2s hook (stops the scroll) -> quote revealed line by line ->
held full quote -> MW logo end card with "follow @mindoverwant".
Music is generated here (simple chord pad + soft pulse), so there is no copyright risk.
"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
BG, INK, GOLD, DIM = (14, 14, 16), (245, 241, 232), (212, 168, 75), (150, 145, 135)
HANDLE = "@mindoverwant"
_fonts = {}


def F(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


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


def background(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # slow drifting gold glow
    cx = W / 2 + 160 * np.sin(t * 0.35)
    cy = H * 0.42 + 120 * np.cos(t * 0.28)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([cx - 420, cy - 420, cx + 420, cy + 420], fill=38)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new("RGB", (W, H), (60, 46, 18)), img, glow)
    d = ImageDraw.Draw(img)
    d.rectangle([48, 48, W - 48, H - 48], outline=(44, 41, 35), width=3)
    return img


def text_center(d, y, text, font, fill, alpha):
    w = font.getlength(text)
    d.text(((W - w) / 2, y), text, font=font, fill=fill + (int(255 * alpha),))


def mark(d, cx, cy, r, alpha):
    a = int(255 * alpha)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD + (a,), width=max(3, r // 22))
    f = F(SERIF, int(r * 0.66))
    wm, ov = f.getlength("M"), int(r * 0.06)
    tot = wm + f.getlength("W") - ov
    x, y = cx - tot / 2, cy - r * 0.45
    d.text((x, y), "M", font=f, fill=INK + (a,))
    d.text((x + wm - ov, y), "W", font=f, fill=GOLD + (a,))


def build_frames(spec):
    hook, lines, gold = spec["hook"], spec["lines"], set(spec.get("gold", []))
    hook_end = 2.2
    per_line = 1.15
    reveal_end = hook_end + 0.3 + per_line * len(lines)
    hold_end = reveal_end + 2.6
    total = hold_end + 2.6
    # layout quote lines (auto-size so the longest fits)
    size = 96
    while max(F(SERIF, size).getlength(l) for l in lines) > W - 200 and size > 50:
        size -= 4
    fq = F(SERIF, size)
    lh = int(size * 1.35)
    y0 = H * 0.46 - (len(lines) * lh) / 2
    fh = F(SERIF, 84)
    hook_lines = wrap(hook, fh, W - 200)
    n = int(total * FPS)
    for i in range(n):
        t = i / FPS
        img = background(t).convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        if t < hook_end:
            a = ease(t / 0.35) * (1 - ease((t - (hook_end - 0.3)) / 0.3))
            hy = H * 0.42 - len(hook_lines) * 55
            for j, hl in enumerate(hook_lines):
                text_center(d, hy + j * 110 + (1 - ease(t / 0.4)) * 40, hl, fh, INK, a)
            d.rectangle([W / 2 - 70, hy + len(hook_lines) * 110 + 30, W / 2 + 70, hy + len(hook_lines) * 110 + 36], fill=GOLD + (int(255 * a),))
        elif t < hold_end:
            lt = t - hook_end - 0.3
            fade_out = 1 - ease((t - (hold_end - 0.35)) / 0.35)
            text_center(d, y0 - 220, "“", F(SERIF, 200), GOLD, ease(lt / 0.5) * fade_out)
            for j, line in enumerate(lines):
                a = ease((lt - j * per_line) / 0.5) * fade_out
                if a <= 0:
                    continue
                rise = (1 - ease((lt - j * per_line) / 0.6)) * 30
                text_center(d, y0 + j * lh + rise, line, fq, GOLD if j in gold else INK, a)
            text_center(d, H - 300, HANDLE, F(SANS, 44), DIM, ease(lt / 0.8) * fade_out)
        else:
            lt = t - hold_end
            a = ease(lt / 0.5)
            mark(d, W / 2, H * 0.40, int(170 + 10 * ease(lt / 1.5)), a)
            text_center(d, H * 0.40 + 240, "MIND OVER WANT", F(SANS, 48), DIM, a)
            a2 = ease((lt - 0.5) / 0.5)
            fb = F(SANS, 56)
            label = "FOLLOW " + HANDLE
            bw = fb.getlength(label) + 100
            by = H * 0.40 + 360
            d.rounded_rectangle([(W - bw) / 2, by, (W + bw) / 2, by + 110], 55, fill=GOLD + (int(255 * a2),))
            text_center(d, by + 24, label, fb, BG, a2)
        img = Image.alpha_composite(img, ov).convert("RGB")
        yield img
    return


def music(path, seconds, sr=44100):
    """Original ambient track: Am - F - C - G pad with a soft pulse."""
    t = np.arange(int(seconds * sr)) / sr
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [130.81, 196.0, 261.63], [196.0, 246.94, 293.66]]
    bar = 2.4
    out = np.zeros_like(t)
    for k, ch in enumerate(chords * 4):
        s, e = k * bar, (k + 1) * bar
        m = (t >= s) & (t < e + 0.6)
        if not m.any():
            continue
        tt = t[m] - s
        env = np.minimum(1, tt / 0.5) * np.exp(-np.maximum(0, tt - bar) * 4)
        for f in ch:
            out[m] += env * (0.5 * np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * 2 * f * tt))
    # soft heartbeat pulse every 0.6 s
    for b in np.arange(0, seconds, 0.6):
        m = (t >= b) & (t < b + 0.25)
        tt = t[m] - b
        out[m] += 0.9 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18)
    fade = np.minimum(1, np.minimum(t / 0.8, (seconds - t) / 1.2))
    out = out * np.clip(fade, 0, 1)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    data = (out * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def main():
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    seconds = 2.2 + 0.3 + 1.15 * len(spec["lines"]) + 2.6 + 2.6
    cover_i = int((2.5 + 1.15 * len(spec["lines"]) + 1.0) * FPS)
    wav = out + ".wav"
    music(wav, seconds + 0.5)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, f in enumerate(build_frames(spec)):
        if i == cover_i:
            f.save(out[:-4] + "_cover.jpg", quality=90)  # cover = held full quote
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(f"reel: {out} ({seconds:.1f}s)")


if __name__ == "__main__":
    main()
