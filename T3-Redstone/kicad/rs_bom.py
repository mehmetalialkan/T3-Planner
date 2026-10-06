#!/usr/bin/env python3
"""rs_design.py -> ../bom/bom.csv  (ayni deger + footprint + MPN gruplanir)"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_design as D          # noqa: E402

OUT = os.path.join(HERE, "..", "bom", "bom.csv")


def natural(r):
    m = re.match(r"([A-Z]+)(\d+)([A-Z]*)", r)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (r, 0, "")


groups = {}
for p in D.PARTS:
    if p["ref"].startswith("MH"):
        continue
    key = (p["value"], p["fp"], p["mpn"])
    groups.setdefault(key, []).append(p)

rows = []
for (val, fp, mpn), ps in groups.items():
    refs = sorted((p["ref"] for p in ps), key=natural)
    notes = {p["desc"] for p in ps}
    note = notes.pop() if len(notes) == 1 else ""      # sadece grubun ortak notu
    rows.append([" ".join(refs), len(refs), val, mpn, fp.split(":")[1], note,
                 "B (alt)" if ps[0]["side"] == "B" else "F (ust)"])
rows.sort(key=lambda r: natural(r[0].split()[0]))
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Ref", "Adet", "Deger", "MPN", "Footprint", "Not", "Yuz"])
    w.writerows(rows)
print(f"BOM: {OUT}  ({len(rows)} satir, {sum(r[1] for r in rows)} parca)")
