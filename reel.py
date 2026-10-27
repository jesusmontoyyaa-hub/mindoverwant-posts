"""
@mindoverwant motivational Reel generator (9:16, original music, optional deep voiceover).

Usage:
  python3 reel.py <reel_json> <out_mp4>

reel_json: {"hook": "Read this if you feel like quitting.",
            "lines": ["Discipline is", "remembering what you want", "more than what you want", "right now."],
            "gold": [2],            # indexes of lines shown in gold (optional)
            "voice": true}          # deep male voiceover reads hook + quote (default false until approved)
Lines are spoken as full sentences (a sentence ends at a line ending in . ! ?) and each
line appears on screen as the voice reaches it. Music is generated here (a different original track per Reel, seeded from its text or an optional "music" int), and the voice is
the offline Piper "ryan" voice, deepened and slowed, so there is no copyright risk.
"""
import json, os, re, subprocess, sys, tarfile, urllib.request, wave, zlib
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
PROGRESSIONS = {
    "minor_epic":   [[0, 3, 7], [8, 12, 15], [3, 7, 10], [10, 14, 17]],   # i VI III VII
    "minor_drive":  [[0, 3, 7], [5, 8, 12], [8, 12, 15], [7, 11, 14]],    # i iv VI V
    "minor_rise":   [[0, 3, 7], [10, 14, 17], [8, 12, 15], [10, 14, 17]], # i VII VI VII
    "minor_dark":   [[0, 3, 7], [7, 10, 14], [8, 12, 15], [5, 8, 12]],    # i v VI iv
    "major_hope":   [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]],    # I V vi IV
    "major_warm":   [[0, 4, 7], [5, 9, 12], [9, 12, 16], [7, 11, 14]],    # I IV vi V
}
TIMBRES = ["pad", "piano", "pluck", "organ"]
BEATS = ["heartbeat", "soft_kick_hat", "halftime", "none"]


def _midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _tone(kind, f, tt, length):
    """One note of a given timbre. tt: time since note start."""
    if kind == "pad":
        env = np.minimum(1, tt / 0.45) * np.exp(-np.maximum(0, tt - length) * 4)
        w = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt)
    elif kind == "piano":
        env = np.minimum(1, tt / 0.006) * np.exp(-tt * 1.6)
        w = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 2) + 0.25 * np.sin(2 * np.pi * 3 * f * tt) * np.exp(-tt * 3)
    elif kind == "pluck":
        env = np.minimum(1, tt / 0.004) * np.exp(-tt * 4.5)
        w = np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 6)
    else:  # organ
        env = np.minimum(1, tt / 0.06) * np.exp(-np.maximum(0, tt - length) * 6)
        w = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 3 * f * tt) + 0.12 * np.sin(2 * np.pi * 5 * f * tt)
    return env * w


def music_track(seconds, sr=44100, seed=0):
    """Original instrumental, different for every seed: key, progression, tempo,
    instrument, arpeggio, bass and beat are all chosen from the seed."""
    rng = np.random.default_rng(seed)
    prog_name = list(PROGRESSIONS)[rng.integers(len(PROGRESSIONS))]
    prog = PROGRESSIONS[prog_name]
    root = int(rng.integers(45, 53))          # A2..E3
    bpm = int(rng.integers(68, 104))
    timbre = TIMBRES[rng.integers(len(TIMBRES))]
    beat_style = BEATS[rng.integers(len(BEATS))]
    use_arp = bool(rng.random() < 0.6)
    use_bass = bool(rng.random() < 0.7)
    beat = 60.0 / bpm
    bar = 4 * beat
    t = np.arange(int(seconds * sr)) / sr
    out = np.zeros_like(t)
    n_bars = int(seconds / bar) + 2
    for k in range(n_bars):
        ch = prog[k % len(prog)]
        s = k * bar
        hold = bar if timbre in ("pad", "organ") else bar
        m = (t >= s) & (t < s + bar + 1.0)
        if not m.any():
            continue
        tt = t[m] - s
        for iv in ch:
            out[m] += 0.32 * _tone(timbre, _midi(root + 12 + iv), tt, hold)
        if use_bass:
            out[m] += 0.45 * _tone("pad" if timbre != "pad" else "organ", _midi(root + ch[0] - 12 if ch[0] < 12 else root + ch[0] - 24), tt, bar) * 0.8
        if use_arp:
            notes = [root + 24 + iv for iv in ch] + [root + 36 + ch[0]]
            step = beat / 2
            for j in range(8):
                a0 = s + j * step
                ma = (t >= a0) & (t < a0 + 1.2)
                if ma.any():
                    out[ma] += 0.16 * _tone("pluck", _midi(notes[j % len(notes)]), t[ma] - a0, step)
    # drums
    noise = rng.standard_normal(len(t))
    hat_src = np.diff(np.concatenate([[0], noise]))  # crude high-pass

    def kick(at, gain=1.0):
        mk = (t >= at) & (t < at + 0.35)
        tk = t[mk] - at
        f = 45 + 75 * np.exp(-tk * 30)
        out[mk] += gain * 0.9 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tk * 12)

    def hat(at, gain=1.0):
        i0 = int(at * sr)
        n = int(0.06 * sr)
        if i0 + n < len(out):
            out[i0:i0 + n] += gain * 0.08 * hat_src[i0:i0 + n] * np.exp(-np.arange(n) / sr * 60)

    def snare(at):
        i0 = int(at * sr)
        n = int(0.18 * sr)
        if i0 + n < len(out):
            out[i0:i0 + n] += 0.22 * noise[i0:i0 + n] * np.exp(-np.arange(n) / sr * 22)

    for k in range(n_bars):
        s = k * bar
        if beat_style == "heartbeat":
            kick(s, 0.9); kick(s + beat * 0.45, 0.6)
            kick(s + 2 * beat, 0.9); kick(s + 2.45 * beat, 0.6)
        elif beat_style == "soft_kick_hat":
            kick(s); kick(s + 2 * beat)
            for j in range(8):
                hat(s + j * beat / 2, 1.0 if j % 2 else 0.6)
        elif beat_style == "halftime":
            kick(s); snare(s + 2 * beat)
            for j in range(4):
                hat(s + j * beat + beat / 2, 0.7)
    fade = np.clip(np.minimum(t / 0.6, (seconds - t) / 1.0), 0, 1)
    out = out * fade
    music_track.last = f"{prog_name}, key {root % 12}, {bpm} bpm, {timbre}, beat={beat_style}, arp={use_arp}, bass={use_bass}"
    out = out / (np.sqrt(np.mean(out ** 2)) + 1e-9) * 0.22  # same loudness for every track
    return np.tanh(out * 1.6) / np.tanh(1.6)  # gentle limiter


def mix(path, seconds, clips, sr=44100, seed=0):
    music = music_track(seconds, sr, seed)
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
    seed = int(spec.get("music", zlib.crc32((spec["hook"] + "|".join(spec["lines"])).encode())))
    mix(wav, tm["total"] + 0.3, clips, seed=seed)
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
    print(f"reel: {out} ({tm['total']:.1f}s, voice={'on' if clips else 'off'}, music: {music_track.last})")


if __name__ == "__main__":
    main()
