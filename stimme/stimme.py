#!/usr/bin/env python3
"""
Vertont alle Sprechertexte in stimme/*.txt mit der freien KI-Stimme Piper (Thorsten, Deutsch).
Format einer Zeile:  0:13|Text, der ab Sekunde 13 gesprochen wird
Ergebnis: stimme/<name>/01.wav, 02.wav, ... plus zeiten.txt
Läuft über GitHub Actions (.github/workflows/stimme.yml).
"""
import glob, hashlib, os, sys, wave

LENGTH_SCALE = 0.85  # < 1 = schneller sprechen (passt besser zu TikTok)
NOISE_SCALE = 0.85   # mehr Ausdruck in der Stimme (Standard 0.667)
NOISE_W = 0.9        # lebendigeres Sprechtempo (Standard 0.8)

from piper import PiperVoice
voice = PiperVoice.load(sys.argv[1])


def synth(text, path):
    with wave.open(path, "wb") as wf:
        if hasattr(voice, "synthesize_wav"):          # piper-tts ab 1.3
            try:
                from piper import SynthesisConfig
                voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(
                    length_scale=LENGTH_SCALE, noise_scale=NOISE_SCALE, noise_w_scale=NOISE_W))
            except ImportError:
                voice.synthesize_wav(text, wf)
        else:                                          # ältere Versionen
            voice.synthesize(text, wf, length_scale=LENGTH_SCALE, noise_scale=NOISE_SCALE, noise_w=NOISE_W)


def seconds(ts):
    parts = [float(p) for p in ts.strip().split(":")]
    return parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0]


here = os.path.dirname(os.path.abspath(__file__))
for txt in sorted(glob.glob(os.path.join(here, "*.txt"))):
    raw = open(txt, encoding="utf-8").read()
    digest = hashlib.sha1(raw.encode()).hexdigest()
    out = os.path.join(here, os.path.splitext(os.path.basename(txt))[0])
    hash_file = os.path.join(out, ".hash")
    if os.path.exists(hash_file) and open(hash_file).read().strip() == digest:
        print(f"{os.path.basename(txt)}: schon vertont")
        continue
    os.makedirs(out, exist_ok=True)
    for old in glob.glob(os.path.join(out, "*.wav")):
        os.remove(old)
    times = []
    lines = [l for l in raw.splitlines() if "|" in l and l.strip()]
    for i, line in enumerate(lines, 1):
        ts, text = line.split("|", 1)
        path = os.path.join(out, f"{i:02d}.wav")
        synth(text.strip(), path)
        times.append(f"{seconds(ts):.2f}|{i:02d}.wav")
        print(f"{os.path.basename(txt)} {i:02d}: {text.strip()[:60]}")
    open(os.path.join(out, "zeiten.txt"), "w").write("\n".join(times) + "\n")
    open(hash_file, "w").write(digest)
