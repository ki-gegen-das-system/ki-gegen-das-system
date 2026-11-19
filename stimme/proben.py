#!/usr/bin/env python3
"""Erzeugt Hörproben verschiedener freier deutscher Piper-Stimmen (stimme/proben/*.wav)."""
import json, os, sys, wave
from piper import PiperVoice

TEXT = "Tag zwei! Bert verkauft Tesla, mit Verlust! Und Kurt? Hat schon wieder keinen einzigen Tipp abgegeben!"
PROBEN = [  # (Name, Modell, Sprecher, Tempo, Ausdruck)
    ("A", "thorsten_emotional", "amused", 0.88, 0.8),
    ("B", "thorsten_emotional", "surprised", 0.88, 0.8),
    ("C", "thorsten", None, 0.85, 0.85),
    ("D", "kerstin", None, 0.88, 0.8),
    ("E", "ramona", None, 0.88, 0.8),
]
d = sys.argv[1]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proben")
os.makedirs(out, exist_ok=True)
for name, model, speaker, ls, ns in PROBEN:
    path = os.path.join(d, f"{model}.onnx")
    voice = PiperVoice.load(path)
    sid = None
    if speaker:
        sid = json.load(open(path + ".json"))["speaker_id_map"][speaker]
    with wave.open(os.path.join(out, f"{name}.wav"), "wb") as wf:
        if hasattr(voice, "synthesize_wav"):
            from piper import SynthesisConfig
            voice.synthesize_wav(f"Stimme {name}. " + TEXT, wf, syn_config=SynthesisConfig(
                speaker_id=sid, length_scale=ls, noise_scale=ns, noise_w_scale=0.9))
        else:
            voice.synthesize(f"Stimme {name}. " + TEXT, wf, speaker_id=sid, length_scale=ls,
                             noise_scale=ns, noise_w=0.9)
    print("fertig:", name, model, speaker or "")
