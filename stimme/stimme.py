#!/usr/bin/env python3
"""
Vertont die Sprechertexte in stimme/*.txt – läuft über GitHub Actions (.github/workflows/stimme.yml).

Stimme: Chatterbox Multilingual (Resemble AI, MIT-Lizenz), Standardstimme, ruhig-natürlich
("X1": exaggeration 0.5, cfg 0.5). Fällt Chatterbox aus, springt Piper (Thorsten) ein.

Zwei Formate werden erkannt:
  Neu (Baukasten v2):  s1|Text   – Szenen-Name, dann ein bis zwei Sätze. Mehrere Zeilen pro Szene erlaubt.
                       Ergebnis: stimme/<name>/NN.wav + clips.json (Szene, Datei, Dauer, Text)
  Alt (Folge 1–3):     0:13|Text – Startzeit in Sekunden. Ergebnis: NN.wav + zeiten.txt
Unveränderte Zeilen werden nicht neu erzeugt (spart Zeit).
"""
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
EXAGGERATION = 0.5   # Stimme X1
CFG_WEIGHT = 0.5
SEED = 7
PIPER_MODEL = os.path.expanduser("~/stimmen/de.onnx")

_engine = None


def engine():
    """Lädt Chatterbox (bevorzugt) oder Piper. Gibt (name, synth_funktion) zurück."""
    global _engine
    if _engine:
        return _engine
    if os.environ.get("STIMME") != "piper":
        try:
            import torch
            _orig = torch.load
            def _cpu_load(*a, **k):
                k.setdefault("map_location", torch.device("cpu"))
                return _orig(*a, **k)
            torch.load = _cpu_load
            import torchaudio as ta
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")

            def synth(text, path):
                torch.manual_seed(SEED)
                wav = model.generate(text, language_id="de", exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
                ta.save(path, wav, model.sr)
            _engine = ("chatterbox", synth)
            return _engine
        except Exception as e:
            print(f"Chatterbox nicht verfügbar ({e}) – nehme Piper.")
    from piper import PiperVoice
    voice = PiperVoice.load(PIPER_MODEL)

    def synth(text, path):
        with wave.open(path, "wb") as wf:
            if hasattr(voice, "synthesize_wav"):
                from piper import SynthesisConfig
                voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(
                    length_scale=0.85, noise_scale=0.85, noise_w_scale=0.9))
            else:
                voice.synthesize(text, wf, length_scale=0.85, noise_scale=0.85, noise_w=0.9)
    _engine = ("piper", synth)
    return _engine


def trim_silence(path, threshold=0.012, pad_s=0.06):
    """Schneidet Stille am Anfang und Ende ab und gibt die Länge in Sekunden zurück."""
    import numpy as np
    import soundfile as sf
    data, sr = sf.read(path)
    mono = data if data.ndim == 1 else data.mean(axis=1)
    loud = np.where(np.abs(mono) > threshold * max(1e-9, np.abs(mono).max()))[0]
    if len(loud):
        a = max(0, loud[0] - int(pad_s * sr))
        b = min(len(mono), loud[-1] + int(pad_s * sr))
        data = data[a:b]
    sf.write(path, data, sr)
    return len(data) / sr


def seconds(ts):
    parts = [float(p) for p in ts.strip().split(":")]
    return parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0]


def process(txt):
    raw = open(txt, encoding="utf-8").read()
    name = os.path.splitext(os.path.basename(txt))[0]
    out = os.path.join(HERE, name)
    lines = [l.strip() for l in raw.splitlines() if "|" in l and l.strip() and not l.startswith("#")]
    if not lines:
        return
    neu = re.match(r"^[A-Za-z]\w*\|", lines[0]) is not None
    digest = hashlib.sha1((raw + "v2").encode()).hexdigest()
    legacy = hashlib.sha1(raw.encode()).hexdigest()   # Hash der alten Version (Folge 1–3)
    hash_file = os.path.join(out, ".hash")
    if os.path.exists(hash_file) and open(hash_file).read().strip() in (digest, legacy):
        print(f"{name}: schon vertont")
        return
    os.makedirs(out, exist_ok=True)
    old = {}
    clips_path = os.path.join(out, "clips.json")
    if os.path.exists(clips_path):
        for c in json.load(open(clips_path, encoding="utf-8")).get("clips", []):
            old[c.get("hash")] = c
    # vorhandene Aufnahmen zur Seite legen, unveränderte Zeilen werden von dort übernommen
    alt = os.path.join(out, ".alt")
    os.makedirs(alt, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*.wav")):
        os.replace(f, os.path.join(alt, os.path.basename(f)))
    eng, synth = engine()
    clips, times, keep = [], [], set()
    for i, line in enumerate(lines, 1):
        tag, text = line.split("|", 1)
        text = text.strip()
        h = hashlib.sha1(f"{eng}|{text}".encode()).hexdigest()
        fname = f"{i:02d}.wav"
        path = os.path.join(out, fname)
        prev = old.get(h)
        if prev and os.path.exists(os.path.join(alt, prev["datei"])):
            shutil.copyfile(os.path.join(alt, prev["datei"]), path)
            dur = prev["dauer"]
            print(f"{name} {i:02d}: unverändert")
        else:
            synth(text, path)
            dur = trim_silence(path) if eng == "chatterbox" else wav_len(path)
            print(f"{name} {i:02d} ({dur:.1f}s): {text[:70]}")
        keep.add(fname)
        clips.append({"szene": tag.strip(), "datei": fname, "dauer": round(dur, 3), "text": text, "hash": h})
        if not neu:
            times.append(f"{seconds(tag):.2f}|{fname}")
    shutil.rmtree(alt, ignore_errors=True)
    json.dump({"stimme": eng, "clips": clips}, open(clips_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if not neu:
        open(os.path.join(out, "zeiten.txt"), "w").write("\n".join(times) + "\n")
    open(hash_file, "w").write(digest)


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "*.txt")))
    for txt in files:
        process(txt)
