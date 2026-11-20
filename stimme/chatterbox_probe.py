#!/usr/bin/env python3
"""Hörproben mit Chatterbox Multilingual (Resemble AI, MIT-Lizenz) – läuft auf GitHub Actions (CPU)."""
import os, sys, time
import torch

_orig_load = torch.load
def _cpu_load(*a, **k):
    k.setdefault("map_location", torch.device("cpu"))
    return _orig_load(*a, **k)
torch.load = _cpu_load

import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

TEXT = ("Tag drei! Bert macht heute zum ersten Mal richtiges Daytrading. "
        "Sein Stop-Loss greift bei minus anderthalb Prozent, der Take-Profit bei plus drei. "
        "Und Kurt? Checkt die Premier League und findet endlich einen Value-Tipp!")
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "proben2")
os.makedirs(out, exist_ok=True)
ref = os.path.join(here, "proben", "C.wav")

t0 = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
print(f"Modell geladen in {time.time()-t0:.0f}s", flush=True)
PROBEN = [  # Name, Referenzstimme, exaggeration, cfg_weight
    ("X1", None, 0.5, 0.5),
    ("X2", None, 0.8, 0.3),
    ("X3", ref, 0.8, 0.3),
]
for name, prompt, ex, cfg in PROBEN:
    t1 = time.time()
    kw = dict(language_id="de", exaggeration=ex, cfg_weight=cfg)
    if prompt:
        kw["audio_prompt_path"] = prompt
    wav = model.generate(TEXT, **kw)
    ta.save(os.path.join(out, f"{name}.wav"), wav, model.sr)
    print(f"{name}: fertig in {time.time()-t1:.0f}s", flush=True)
