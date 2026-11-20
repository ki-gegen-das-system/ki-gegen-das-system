#!/usr/bin/env python3
"""Hörproben: Chatterbox mit ECHTER deutscher Referenzstimme (Thorsten-Voice, CC0) statt Standardstimme.
Lädt den Thorsten-Voice-Emotional-Datensatz (CC0, Thorsten Müller), baut Referenzen und erzeugt Proben."""
import glob, os, random, sys, tarfile, time
import numpy as np
import soundfile as sf
import torch

_orig = torch.load
def _cpu_load(*a, **k):
    k.setdefault("map_location", torch.device("cpu"))
    return _orig(*a, **k)
torch.load = _cpu_load

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # stimme/
OUT = os.path.join(HERE, "proben3")
REF = os.path.join(HERE, "referenz")
os.makedirs(OUT, exist_ok=True)
os.makedirs(REF, exist_ok=True)
TEXT = ("Tag drei! Bert macht heute Daytrading. Sein Stop-Loss greift bei minus anderthalb Prozent, "
        "der Take-Profit bei plus drei. Und Kurt? Checkt die Premier League und findet endlich einen Value-Tipp!")

# 1) Datensatz entpacken und nach Emotion sortieren
tf = tarfile.open(sys.argv[1], "r:gz")
tf.extractall("/tmp/emo")
wavs = glob.glob("/tmp/emo/**/*.wav", recursive=True)
print("WAVs:", len(wavs), "Beispiel:", wavs[:3])
groups = {}
for w in wavs:
    parts = [p.lower() for p in w.split(os.sep)]
    for emo in ("amused", "neutral", "surprised"):
        if emo in parts or any(emo in p for p in parts[-2:]):
            groups.setdefault(emo, []).append(w)
print({k: len(v) for k, v in groups.items()})

def build_ref(emo, n=3, seed=1):
    files = sorted(groups[emo])
    random.Random(seed).shuffle(files)
    chunks, sr = [], None
    for f in files:
        d, s = sf.read(f)
        if d.ndim > 1:
            d = d.mean(axis=1)
        if sr is None:
            sr = s
        if s != sr:
            continue
        chunks += [d, np.zeros(int(0.35 * sr))]
        if sum(len(c) for c in chunks) / sr > 11:
            break
    ref = np.concatenate(chunks)
    path = os.path.join(REF, f"thorsten_{emo}.wav")
    sf.write(path, ref, sr)
    print(f"Referenz {emo}: {len(ref) / sr:.1f}s")
    return path

refs = {emo: build_ref(emo) for emo in ("neutral", "amused") if emo in groups}

# 2) Chatterbox mit Referenz
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
PROBEN = [("N1", refs.get("neutral"), 0.5, 0.5), ("N2", refs.get("amused"), 0.5, 0.5), ("N3", refs.get("amused"), 0.7, 0.4)]
for name, ref, ex, cfg in PROBEN:
    if not ref:
        continue
    torch.manual_seed(7)
    t0 = time.time()
    wav = model.generate(TEXT, language_id="de", audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg)
    ta.save(os.path.join(OUT, f"{name}.wav"), wav, model.sr)
    print(f"{name}: {time.time() - t0:.0f}s")

# 3) Alte Stimme C (Piper) mit demselben Text
try:
    import wave
    from piper import PiperVoice, SynthesisConfig
    v = PiperVoice.load(os.path.expanduser("~/stimmen/de.onnx"))
    with wave.open(os.path.join(OUT, "C.wav"), "wb") as wf:
        v.synthesize_wav(TEXT, wf, syn_config=SynthesisConfig(length_scale=0.85, noise_scale=0.85, noise_w_scale=0.9))
except Exception as e:
    print("Piper:", e)

# 4) Mit Whisper gegenhören (Hinweis auf Aussprache)
from faster_whisper import WhisperModel
wm = WhisperModel("small", device="cpu", compute_type="int8")
for f in sorted(glob.glob(os.path.join(OUT, "*.wav"))):
    segs, _ = wm.transcribe(f, language="de", beam_size=5)
    print(os.path.basename(f), "->", " ".join(s.text.strip() for s in segs))
