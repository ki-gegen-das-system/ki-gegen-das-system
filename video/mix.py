#!/usr/bin/env python3
"""Legt die Sprach-Clips (zeiten.txt) an ihre Startzeiten ins Video. Nutzung: mix.py video.mp4 stimmordner out.mp4"""
import os, subprocess, sys
video, folder, out = sys.argv[1:4]
LEAD = 0.15
def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())
vdur = dur(video)
items = []
for line in open(os.path.join(folder, "zeiten.txt")):
    if "|" in line:
        t, f = line.strip().split("|")
        items.append((float(t) + LEAD, os.path.join(folder, f)))
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video]
filters, labels = [], []
for i, (start, path) in enumerate(items):
    end = items[i + 1][0] - 0.1 if i + 1 < len(items) else vdur - 0.2
    d = dur(path)
    tempo = min(1.3, max(1.0, d / (end - start)))
    if tempo > 1.0:
        print(f"{os.path.basename(path)}: {d:.2f}s -> {tempo:.2f}x schneller")
    cmd += ["-i", path]
    ms = int(start * 1000)
    filters.append(f"[{i+1}:a]aresample=44100,atempo={tempo:.3f},adelay={ms}|{ms},volume=1.2[a{i}]")
    labels.append(f"[a{i}]")
filters.append("".join(labels) + f"amix=inputs={len(items)}:normalize=0,pan=stereo|c0=c0|c1=c0,alimiter=limit=0.89:level=false,"
               f"apad,atrim=0:{vdur:.3f}[voice]")
tmp = out.replace(".mp4", ".tmp.mp4")
cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[voice]", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]
subprocess.check_call(cmd)
os.replace(tmp, out)
print("fertig:", out, f"{dur(out):.1f}s")
