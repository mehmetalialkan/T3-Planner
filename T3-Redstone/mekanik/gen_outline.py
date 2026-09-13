#!/usr/bin/env python3
"""
T3-Redstone kart konturu + montaj delikleri -> DXF (R12 ASCII)

Olculer T3 Gemstone O1'in kendi Fritzing PCB dosyasindan olculdu
(t3gemstone/hardware/fritzing/t3-gem-o1-pcb.svg, 72 birim/inch):
    kart            : 85.00 x 56.00 mm
    kose yaricapi   : 3.00 mm
    delik araligi   : 58.0 x 49.0 mm
    sol kenardan    : 3.50 mm
Bu degerler Raspberry Pi Model B form faktoruyle birebir ayni.

Koordinat sistemi: sol-alt kose (0,0), Y yukari (DXF standardi).
KiCad'de: Dosya > Ice Aktar > Grafikler ile Edge.Cuts katmanina alinir.
"""
W, H, R = 85.0, 56.0, 3.0
HOLE_D  = 2.75                      # M2.5 icin
HOLES   = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]

# Kamera/DSI FPC kesiti - alt kenara acik. DOGRULA (bkz. kicad/gen_kicad.py)
CUT_X1, CUT_X2, CUT_DEPTH = 42.0, 60.0, 14.0

# 40-pin header: Gemstone'un Fritzing dosyasindan olculen konum.
# DOGRULA - el yapimi bir Fritzing parcasindan geliyor, resmi RPi HAT
# sablonuyla veya kumpasla teyit et. Referans katmanina yaziliyor.
HDR_PIN1 = (8.366, 56.0 - 4.359)    # pin 1 merkezi
HDR_PITCH = 2.54

ent = []
def line(x1, y1, x2, y2, layer):
    ent.append(f"0\nLINE\n8\n{layer}\n10\n{x1:.4f}\n20\n{y1:.4f}\n11\n{x2:.4f}\n21\n{y2:.4f}\n")
def arc(cx, cy, r, a1, a2, layer):
    ent.append(f"0\nARC\n8\n{layer}\n10\n{cx:.4f}\n20\n{cy:.4f}\n40\n{r:.4f}\n50\n{a1:.4f}\n51\n{a2:.4f}\n")
def circle(cx, cy, r, layer):
    ent.append(f"0\nCIRCLE\n8\n{layer}\n10\n{cx:.4f}\n20\n{cy:.4f}\n40\n{r:.4f}\n")

E = "Edge_Cuts"
line(R, 0, CUT_X1, 0, E)            # alt kenar, kesitin solu
line(CUT_X2, 0, W - R, 0, E)        # alt kenar, kesitin sagi
line(CUT_X1, 0, CUT_X1, CUT_DEPTH, E)          # kesit sol duvar
line(CUT_X1, CUT_DEPTH, CUT_X2, CUT_DEPTH, E)  # kesit tavani
line(CUT_X2, CUT_DEPTH, CUT_X2, 0, E)          # kesit sag duvar
line(W, R, W, H - R, E)             # sag
line(W - R, H, R, H, E)             # ust
line(0, H - R, 0, R, E)             # sol
arc(W - R, R,     R, 270, 360, E)   # sag-alt
arc(W - R, H - R, R,   0,  90, E)   # sag-ust
arc(R,     H - R, R,  90, 180, E)   # sol-ust
arc(R,     R,     R, 180, 270, E)   # sol-alt
for x, y in HOLES:
    circle(x, y, HOLE_D / 2, "Holes")
for i in range(20):                 # 2x20 header referansi
    x = HDR_PIN1[0] + i * HDR_PITCH
    circle(x, HDR_PIN1[1],             0.5, "REF_Header_DOGRULA")
    circle(x, HDR_PIN1[1] + HDR_PITCH, 0.5, "REF_Header_DOGRULA")

dxf = "0\nSECTION\n2\nENTITIES\n" + "".join(ent) + "0\nENDSEC\n0\nEOF\n"
open("t3-redstone-outline.dxf", "w").write(dxf)
print(f"yazildi: t3-redstone-outline.dxf  ({len(ent)} varlik, {W}x{H} mm)")
