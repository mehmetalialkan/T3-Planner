#!/usr/bin/env python3
"""Karttan onizleme: kicad-cli ile SVG (ve rsvg-convert varsa PNG).

    python3 rs_render.py [cikis_adi] [katmanlar]
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "t3-redstone.kicad_pcb")
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "mekanik", "t3-redstone-preview")
layers = sys.argv[2] if len(sys.argv) > 2 else "F.Cu,B.Cu,F.SilkS,F.Mask,Edge.Cuts"
svg = out + ".svg"
subprocess.run(["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2",
                "--exclude-drawing-sheet", "-o", svg, PCB], check=True,
               stdout=subprocess.DEVNULL)
print("svg:", svg)
if shutil.which("rsvg-convert") and "--png" in sys.argv:
    subprocess.run(["rsvg-convert", "-z", "6", "-b", "white", "-o", out + ".png", svg], check=True)
    print("png:", out + ".png")
