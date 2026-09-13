#!/usr/bin/env python3
"""T3-Redstone icin acilabilir bir KiCad 8 board dosyasi uretir."""
import uuid as _u
def U(): return str(_u.uuid4())

# --- Mekanik (Gemstone O1'in kendi Fritzing dosyasindan olculdu) -------------
HAT_W, HAT_H, HAT_R = 85.0, 56.0, 3.0      # TAM BOY - Gemstone ile ayni
GEM_W, GEM_H        = 85.0, 56.0           # Gemstone O1 konturu (ayni)

# Kamera/DSI FPC konnektorleri icin alt kenardan acik kesit.
# !!! DOGRULA: bu degerler fotograftan tahmin edildi. Gemstone'un alt kenari ile
# J4 (CSI) ve J12 (CSI/DSI) konnektorleri arasini kumpasla olc, asagidaki dort
# sayiyi guncelle, betigi tekrar calistir. Kesit alt kenara acik birakildi:
# hem FPC kablosu disari cikar hem mandala parmak girer hem de frezelemesi kolay.
CUT_X1, CUT_X2 = 42.0, 60.0                # kesitin X araligi (sol kenardan)
CUT_DEPTH      = 14.0                      # alt kenardan yukari derinlik
CUT_R          = 1.5                       # ic kose yaricapi (freze ucu >= 2mm)

# Gemstone'un yuksek konnektorleri - shield bunlarin UZERINDEN gecer.
# Bu yuzden YUKSEK disi header sart (>=16mm gecis yuksekligi).
TALL = [("USB-A x3 yigini", 68.0, 20.0, 85.0, 52.0),
        ("RJ45 Gigabit",    60.0,  0.0, 85.0, 18.0)]
HOLES  = [(3.5,3.5),(61.5,3.5),(3.5,52.5),(61.5,52.5)]
PIN1   = (8.366, 51.641)                   # pin1 merkezi, HAT sol-alttan
PITCH  = 2.54
ORG    = (50.0, 50.0)                      # sayfa uzerinde kart sol-alt kosesi

def X(x): return ORG[0] + x
def Y(y): return ORG[1] + (HAT_H - y)      # KiCad Y asagi

out = []
def w(s): out.append(s)

w('(kicad_pcb (version 20240108) (generator "t3-redstone-gen") (generator_version "8.0")')
w('  (general (thickness 1.6) (legacy_teardrops no))')
w('  (paper "A4")')
w('  (title_block (title "T3-Redstone") (rev "A") (company "T3 Gemstone O1 shield")')
w('    (comment 1 "Kart konturu ve montaj delikleri dogrulandi")')
w('    (comment 2 "40-pin header konumu: Fritzing olcumu, kumpasla teyit et"))')
w('  (layers')
for n,nm,ty in [(0,"F.Cu","signal"),(1,"In1.Cu","signal"),(2,"In2.Cu","signal"),(31,"B.Cu","signal"),
    (32,"B.Adhes","user"),(33,"F.Adhes","user"),(34,"B.Paste","user"),(35,"F.Paste","user"),
    (36,"B.SilkS","user"),(37,"F.SilkS","user"),(38,"B.Mask","user"),(39,"F.Mask","user"),
    (40,"Dwgs.User","user"),(41,"Cmts.User","user"),(42,"Eco1.User","user"),(43,"Eco2.User","user"),
    (44,"Edge.Cuts","user"),(45,"Margin","user"),(46,"B.CrtYd","user"),(47,"F.CrtYd","user"),
    (48,"B.Fab","user"),(49,"F.Fab","user")]:
    w(f'    ({n} "{nm}" {ty})')
w('  )')
w('  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no)')
w('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000)')
w('      (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes) (usegerberadvancedattributes yes)')
w('      (creategerberjobfile yes) (dashed_line_dash_ratio 12.000000) (dashed_line_gap_ratio 3.000000)')
w('      (svgprecision 4) (plotframeref no) (viasonmask no) (mode 1) (useauxorigin no) (hpglpennumber 1)')
w('      (hpglpenspeed 20) (hpglpendiameter 15.000000) (pdf_front_fp_property_popups yes) (pdf_back_fp_property_popups yes)')
w('      (dxfpolygonmode yes) (dxfimperialunits yes) (dxfusepcbnewfont yes) (psnegative no) (psa4output no)')
w('      (plotreference yes) (plotvalue yes) (plotfptext yes) (plotinvisibletext no) (sketchpadsonfab no)')
w('      (subtractmaskfromsilk no) (outputformat 1) (mirror no) (drillshape 1) (scaleselection 1) (outputdirectory "")))')
w('  (net 0 "")')

def gr_line(x1,y1,x2,y2,layer,width=0.1):
    w(f'  (gr_line (start {X(x1):.4f} {Y(y1):.4f}) (end {X(x2):.4f} {Y(y2):.4f}) '
      f'(stroke (width {width}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
def gr_arc(cx,cy,r,a1,a2,layer,width=0.1):
    import math
    p=lambda a:(cx+r*math.cos(math.radians(a)), cy+r*math.sin(math.radians(a)))
    s,m,e=p(a1),p((a1+a2)/2),p(a2)
    w(f'  (gr_arc (start {X(s[0]):.4f} {Y(s[1]):.4f}) (mid {X(m[0]):.4f} {Y(m[1]):.4f}) '
      f'(end {X(e[0]):.4f} {Y(e[1]):.4f}) (stroke (width {width}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
def gr_text(t,x,y,layer,size=1.5,thick=0.25):
    w(f'  (gr_text "{t}" (at {X(x):.4f} {Y(y):.4f}) (layer "{layer}") (uuid "{U()}") '
      f'(effects (font (size {size} {size}) (thickness {thick}))))')

# --- Edge.Cuts: HAT konturu -------------------------------------------------
E="Edge.Cuts"
gr_line(HAT_R,0,HAT_W-HAT_R,0,E); gr_line(HAT_W,HAT_R,HAT_W,HAT_H-HAT_R,E)
gr_line(HAT_W-HAT_R,HAT_H,HAT_R,HAT_H,E); gr_line(0,HAT_H-HAT_R,0,HAT_R,E)
gr_arc(HAT_W-HAT_R,HAT_R,HAT_R,270,360,E); gr_arc(HAT_W-HAT_R,HAT_H-HAT_R,HAT_R,0,90,E)
gr_arc(HAT_R,HAT_H-HAT_R,HAT_R,90,180,E);  gr_arc(HAT_R,HAT_R,HAT_R,180,270,E)

# --- Kamera/DSI kesiti: alt kenara acik U ----------------------------------
# Alt kenar cizgisini kesit kadar bolmek icin yukaridaki alt cizgiyi sil ve
# iki parcaya ayir.
out[:] = [l for l in out if not (l.startswith('  (gr_line') and
          f'(start {X(HAT_R):.4f} {Y(0):.4f}) (end {X(HAT_W-HAT_R):.4f} {Y(0):.4f})' in l)]
gr_line(HAT_R,0,CUT_X1,0,E)                 # alt kenar, kesitin solu
gr_line(CUT_X2,0,HAT_W-HAT_R,0,E)           # alt kenar, kesitin sagi
gr_line(CUT_X1,0,CUT_X1,CUT_DEPTH-CUT_R,E)  # kesit sol duvar
gr_line(CUT_X2,CUT_DEPTH-CUT_R,CUT_X2,0,E)  # kesit sag duvar
gr_line(CUT_X1+CUT_R,CUT_DEPTH,CUT_X2-CUT_R,CUT_DEPTH,E)   # kesit tavani
gr_arc(CUT_X1+CUT_R,CUT_DEPTH-CUT_R,CUT_R,180,90,E)
gr_arc(CUT_X2-CUT_R,CUT_DEPTH-CUT_R,CUT_R,90,0,E)

# --- Dwgs.User: altta duran Gemstone O1 konturu (referans) ------------------
D="Dwgs.User"
gr_text("SHIELD = GEMSTONE O1 TAM BOY 85x56",30,-3.0,D,1.2)
for nm,x1,y1,x2,y2 in TALL:
    gr_line(x1,y1,x2,y1,D,0.3); gr_line(x2,y1,x2,y2,D,0.3)
    gr_line(x2,y2,x1,y2,D,0.3); gr_line(x1,y2,x1,y1,D,0.3)
    gr_text(f"{nm} - h~13.5mm - YUKSEK HEADER SART",(x1+x2)/2,(y1+y2)/2,D,1.0)

# --- Montaj delikleri (NPTH) -----------------------------------------------
for i,(hx,hy) in enumerate(HOLES,1):
    w(f'  (footprint "MountingHole:MountingHole_2.7mm_M2.5" (layer "F.Cu") (uuid "{U()}") '
      f'(at {X(hx):.4f} {Y(hy):.4f})')
    w(f'    (property "Reference" "MH{i}" (at 0 -3.4 0) (layer "F.SilkS") (uuid "{U()}") '
      f'(effects (font (size 1 1) (thickness 0.15))))')
    w(f'    (property "Value" "M2.5" (at 0 3.4 0) (layer "F.Fab") (hide yes) (uuid "{U()}") '
      f'(effects (font (size 1 1) (thickness 0.15))))')
    w(f'    (attr exclude_from_pos_files exclude_from_bom)')
    w(f'    (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "F&B.Cu" "*.Mask") (uuid "{U()}"))')
    w(f'    (fp_circle (center 0 0) (end 3.2 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.CrtYd") (uuid "{U()}"))')
    w('  )')

# --- 2x20 header ------------------------------------------------------------
w(f'  (footprint "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" (layer "F.Cu") (uuid "{U()}") '
  f'(at {X(PIN1[0]):.4f} {Y(PIN1[1]):.4f})')
w(f'    (property "Reference" "J1" (at 0 -3 0) (layer "F.SilkS") (uuid "{U()}") '
  f'(effects (font (size 1 1) (thickness 0.15))))')
w(f'    (property "Value" "GEMSTONE_40PIN_DISI_YUKSEK" (at 24 5 0) (layer "F.Fab") (uuid "{U()}") '
  f'(effects (font (size 1 1) (thickness 0.15))))')
for i in range(20):
    px = i*PITCH
    for row,pn in ((0,2*i+1),(1,2*i+2)):
        shape = "rect" if pn==1 else "circle"
        py = -row*PITCH   # pin1 alt sira, pin2 ust sira (kart ust kenarina dogru)
        w(f'    (pad "{pn}" thru_hole {shape} (at {px:.3f} {py:.3f}) (size 1.7 1.7) (drill 1.0) '
          f'(layers "*.Cu" "*.Mask") (uuid "{U()}"))')
w(f'    (fp_line (start -1.8 1.8) (end {19*PITCH+1.8:.3f} 1.8) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{U()}"))')
w(f'    (fp_line (start -1.8 -4.34) (end {19*PITCH+1.8:.3f} -4.34) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{U()}"))')
w('  )')

# --- Ipek baski notlari -----------------------------------------------------
S="F.SilkS"
gr_text("T3-REDSTONE",4,46,S,2.5,0.4)
gr_text("ROS2 Robot Kontrol Karti / Gemstone O1",4,42,S,1.2)
gr_text("2S LiPo ONLY (6.0-8.4V)",4,39,S,1.2)
gr_text("KAMERA / DSI ERISIMI",CUT_X1+1,CUT_DEPTH+2.5,S,1.2)
w(')')
open("t3-redstone.kicad_pcb","w").write("\n".join(out)+"\n")

# --- proje dosyasi ----------------------------------------------------------
open("t3-redstone.kicad_pro","w").write('{\n  "board": {"3dviewports": [], "design_settings": {}},\n'
  '  "meta": {"filename": "t3-redstone.kicad_pro", "version": 1},\n'
  '  "pcbnew": {"page_layout_descr_file": ""},\n  "sheets": [], "text_variables": {}\n}\n')

# parantez dengesi kontrolu
s=open("t3-redstone.kicad_pcb").read()
print(f"yazildi: t3-redstone.kicad_pcb  ({len(out)} satir)")
print(f"parantez dengesi: ac={s.count('(')} kapa={s.count(')')} -> {'OK' if s.count('(')==s.count(')') else 'HATA'}")
