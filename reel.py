"""
@mindoverwant motivational Reel generator (9:16, original music, optional deep voiceover).

Usage:
  python3 reel.py <reel_json> <out_mp4>

reel_json: {"hook": "Read this if you feel like quitting.",
            "lines": ["Discipline is", "remembering what you want", "more than what you want", "right now."],
            "gold": [2],            # indexes of lines shown in gold (optional)
            "voice": true}          # deep male voiceover reads hook + quote (default false until approved)
Lines are spoken as full sentences (a sentence ends at a line ending in . ! ?) and each
line appears on screen as the voice reaches it. Music is generated here, and the voice is
the offline Piper "ryan" voice, deepened and slowed, so there is no copyright risk.
"""
import json, os, re, subprocess, sys, tarfile, urllib.request, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
BG, INK, GOLD, DIM = (14, 14, 16), (245, 241, 232), (212, 168, 75), (150, 145, 135)
HANDLE = "@mindoverwant"
TTS_DIR = os.environ.get("MOW_TTS_DIR", "/home/claude/tts")
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz"
VOICE_FX = "asetrate=22050*0.88,aresample=44100,atempo=1/0.88,bass=g=4:f=120,aecho=0.8:0.6:45:0.12"
_fonts = {}


# ---------- voice ----------
def ensure_tts():
    piper = os.path.join(TTS_DIR, "piper", "piper")
    model = os.path.join(TTS_DIR, "ryan", "en-us-ryan-high.onnx")
    if not os.path.exists(piper):
        os.makedirs(TTS_DIR, exist_ok=True)
        p = os.path.join(TTS_DIR, "piper.tar.gz")
        urllib.request.urlretrieve(PIPER_URL, p)
        tarfile.open(p).extractall(TTS_DIR)
    if not os.path.exists(model):
        d = os.path.join(TTS_DIR, "ryan")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(TTS_DIR, "ryan.tar.gz")
        urllib.request.urlretrieve(VOICE_URL, p)
        tarfile.open(p).extractall(d)
    return piper, model


def speak(text, path):
    """Synthesize one chunk with the deep, slowed voice. Returns duration in seconds."""
    piper, model = ensure_tts()
    raw = path + ".raw.wav"
    subprocess.run([piper, "--model", model, "--length_scale", "1.2", "--sentence_silence", "0", "--output_file", raw],
                   input=text.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", VOICE_FX, "-ar", "44100", "-ac", "1", path], check=True)
    os.remove(raw)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def sentences(lines):
    """Group line indexes into spoken sentences."""
    groups, cur = [], []
    for i, l in enumerate(lines):
        cur.append(i)
        if re.search(r"[.!?]['\"”]?$", l.strip()):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def plan_timing(spec, workdir):
    """Returns (timing dict, voice clips [(start_s, wav_path)])."""
    lines = spec["lines"]
    clips = []
    if spec.get("voice", False):
        t = 0.4
        hook_wav = os.path.join(workdir, "v_hook.wav")
        hd = speak(spec["hook"], hook_wav)
        clips.append((t, hook_wav))
        hook_end = t + hd + 0.5
        t = hook_end + 0.35
        quote_start = t
        line_at = [0.0] * len(lines)
        for k, grp in enumerate(sentences(lines)):
            text = " ".join(lines[i] for i in grp)
            wp = os.path.join(workdir, f"v_{k}.wav")
            d = speak(text, wp)
            clips.append((t, wp))
            total_chars = sum(len(lines[i]) + 1 for i in grp)
            done = 0
            for i in grp:
                line_at[i] = t + d * (done / total_chars) * 0.92
                done += len(lines[i]) + 1
            t += d + 0.45
        hold_end = t + 1.4
    else:
        hook_end = 1.5
        quote_start = hook_end + 0.15
        line_at = [quote_start + 0.8 * i for i in range(len(lines))]
        hold_end = quote_start + 0.8 * len(lines) + 1.8
    total = hold_end + 1.8
    return {"hook_end": hook_end, "quote_start": quote_start, "line_at": line_at,
            "hold_end": hold_end, "total": total}, clips


# ---------- visuals ----------
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
    cx = W / 2 + 160 * np.sin(t * 0.35)
    cy = H * 0.42 + 120 * np.cos(t * 0.28)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([cx - 420, cy - 420, cx + 420, cy + 420], fill=38)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new("RGB", (W, H), (60, 46, 18)), img, glow)
    ImageDraw.Draw(img).rectangle([48, 48, W - 48, H - 48], outline=(44, 41, 35), width=3)
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


def build_frames(spec, tm):
    hook, lines, gold = spec["hook"], spec["lines"], set(spec.get("gold", []))
    hook_end, q0, line_at, hold_end, total = tm["hook_end"], tm["quote_start"], tm["line_at"], tm["hold_end"], tm["total"]
    size = 96
    while max(F(SERIF, size).getlength(l) for l in lines) > W - 200 and size > 50:
        size -= 4
    fq = F(SERIF, size)
    lh = int(size * 1.35)
    y0 = H * 0.46 - (len(lines) * lh) / 2
    fh = F(SERIF, 84)
    hook_lines = wrap(hook, fh, W - 200)
    for i in range(int(total * FPS)):
        t = i / FPS
        img = background(t).convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        if t < hook_end:
            a = (1 - ease((t - (hook_end - 0.3)) / 0.3))
            hy = H * 0.42 - len(hook_lines) * 55
            for j, hl in enumerate(hook_lines):
                text_center(d, hy + j * 110, hl, fh, INK, a)
            yb = hy + len(hook_lines) * 110 + 30
            d.rectangle([W / 2 - 70, yb, W / 2 + 70, yb + 6], fill=GOLD + (int(255 * a),))
        elif t < hold_end:
            fade_out = 1 - ease((t - (hold_end - 0.35)) / 0.35)
            text_center(d, y0 - 220, "“", F(SERIF, 200), GOLD, ease((t - hook_end) / 0.5) * fade_out)
            for j, line in enumerate(lines):
                lt = t - line_at[j]
                a = ease(lt / 0.45) * fade_out
                if a <= 0:
                    continue
                text_center(d, y0 + j * lh + (1 - ease(lt / 0.55)) * 30, line, fq, GOLD if j in gold else INK, a)
            text_center(d, H - 300, HANDLE, F(SANS, 44), DIM, ease((t - q0) / 0.8) * fade_out)
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
        yield Image.alpha_composite(img, ov).convert("RGB")


# ---------- audio ----------
def music_track(seconds, sr=44100):
    """Original ambient track: Am - F - C - G pad with a soft pulse."""
    t = np.arange(int(seconds * sr)) / sr
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [130.81, 196.0, 261.63], [196.0, 246.94, 293.66]]
    bar = 2.4
    out = np.zeros_like(t)
    for k in range(int(seconds / bar) + 2):
        ch = chords[k % 4]
        s = k * bar
        m = (t >= s) & (t < s + bar + 0.6)
        if not m.any():
            continue
        tt = t[m] - s
        env = np.minimum(1, tt / 0.5) * np.exp(-np.maximum(0, tt - bar) * 4)
        for f in ch:
            out[m] += env * (0.5 * np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * 2 * f * tt))
    for b in np.arange(0, seconds, 0.6):
        m = (t >= b) & (t < b + 0.25)
        tt = t[m] - b
        out[m] += 0.9 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18)
    fade = np.clip(np.minimum(t / 0.8, (seconds - t) / 1.2), 0, 1)
    out = out * fade
    return out / (np.abs(out).max() + 1e-9)


def mix(path, seconds, clips, sr=44100):
    music = music_track(seconds, sr)
    voice = np.zeros_like(music)
    for start, wp in clips:
        v = read_wav(wp)
        i = int(start * sr)
        n = min(len(v), len(voice) - i)
        if n > 0:
            voice[i:i + n] += v[:n]
    if clips:
        voice = voice / (np.abs(voice).max() + 1e-9) * 0.95
        # duck music under the voice
        env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode="same")
        duck = 1 - 0.55 * np.clip(env * 8, 0, 1)
        out = music * 0.30 * duck + voice
    else:
        out = music * 0.6
    out = out / max(1.0, np.abs(out).max())
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    spec = json.load(open(sys.argv[1]))
    out = os.path.abspath(sys.argv[2])
    workdir = os.path.dirname(out)
    os.makedirs(workdir, exist_ok=True)
    tm, clips = plan_timing(spec, workdir)
    wav = out + ".wav"
    mix(wav, tm["total"] + 0.3, clips)
    for _, wp in clips:
        os.remove(wp)
    cover_i = int((tm["hold_end"] - 0.8) * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, f in enumerate(build_frames(spec, tm)):
        if i == cover_i:
            f.save(out[:-4] + "_cover.jpg", quality=90)
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(f"reel: {out} ({tm['total']:.1f}s, voice={'on' if clips else 'off'})")


if __name__ == "__main__":
    main()
