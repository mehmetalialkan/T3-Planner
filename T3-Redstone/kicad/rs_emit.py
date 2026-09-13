"""T3-Redstone -> .kicad_pcb uretici."""
import math, sys
from rs_lib import *
import rs_design as D

ORG = (30.0, 30.0)                       # kart sol-alt kosesinin sayfa konumu
def PX(x): return ORG[0] + x
def PY(y): return ORG[1] + (D.BH - y)

out=[]
def w(s): out.append(s)


# --------------------------------------------- origin normalizasyonu
def _rot0(px,py,deg):
    a=math.radians(deg)
    return (px*math.cos(a)+py*math.sin(a), -px*math.sin(a)+py*math.cos(a))

_OFF={}
def offset(c):
    """Pad kutusu (c.x,c.y) merkezli olsun diye footprint origin kaymasi."""
    if c["ref"] in _OFF: return _OFF[c["ref"]]
    pads,_=c["fp"](*c["args"])
    xs=[];ys=[]
    for p in pads:
        dx,dy=_rot0(p[1],p[2],c["rot"]); pw,ph=p[3],p[4]
        if c["rot"]%180: pw,ph=ph,pw
        xs+=[dx-pw/2,dx+pw/2]; ys+=[dy-ph/2,dy+ph/2]
    o=(0.0,0.0) if c.get("anchor")=="pin1" else (-(min(xs)+max(xs))/2, -(min(ys)+max(ys))/2)
    _OFF[c["ref"]]=o
    return o

# ------------------------------------------------------------------ netler
nets = ["GND"]
for c in D.C:
    for n in c["nets"].values():
        if n and n not in nets: nets.append(n)
NETI = {n:i+1 for i,n in enumerate(nets)}

# ------------------------------------------------- yerlesim cakisma kontrolu
# --------------------------------------------------------------- dosya basi
w('(kicad_pcb (version 20240108) (generator "t3-redstone") (generator_version "8.0")')
w('  (general (thickness 1.6) (legacy_teardrops no))')
w('  (paper "A4")')
w('  (title_block (title "T3-Redstone") (rev "A")')
w('    (company "ROS2 Robot Kontrol Karti - T3 Gemstone O1")')
w('    (comment 1 "4 katman / KIRMIZI maske / ENIG / 1.6mm")')
w('    (comment 2 "F.Cu sinyal - In1.Cu GND - In2.Cu guc - B.Cu sinyal")')
w('    (comment 3 "Entegre pinoutlari veri sayfasindan DOGRULANMALI"))')
w('  (layers')
for n,nm,ty in LAYERS: w(f'    ({n} "{nm}" {ty})')
w('  )')
w('  (setup')
w(STACKUP)
w('    (pad_to_mask_clearance 0.05)')
w('    (allow_soldermask_bridges_in_footprints no)')
w('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000)')
w('      (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes)')
w('      (usegerberadvancedattributes yes) (creategerberjobfile yes)')
w('      (dashed_line_dash_ratio 12.000000) (dashed_line_gap_ratio 3.000000) (svgprecision 4)')
w('      (plotframeref no) (viasonmask no) (mode 1) (useauxorigin no) (hpglpennumber 1)')
w('      (hpglpenspeed 20) (hpglpendiameter 15.000000) (pdf_front_fp_property_popups yes)')
w('      (pdf_back_fp_property_popups yes) (dxfpolygonmode yes) (dxfimperialunits yes)')
w('      (dxfusepcbnewfont yes) (psnegative no) (psa4output no) (plotreference yes)')
w('      (plotvalue yes) (plotfptext yes) (plotinvisibletext no) (sketchpadsonfab no)')
w('      (subtractmaskfromsilk no) (outputformat 1) (mirror no) (drillshape 1)')
w('      (scaleselection 1) (outputdirectory "gerber/")))')
for n,i in NETI.items(): w(f'  (net {i} "{n}")')
w('  (net 0 "")')

# --------------------------------------------------------------- Edge.Cuts
def gline(x1,y1,x2,y2,layer,wdt=0.1):
    w(f'  (gr_line (start {PX(x1):.4f} {PY(y1):.4f}) (end {PX(x2):.4f} {PY(y2):.4f}) '
      f'(stroke (width {wdt}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
def garc(cx,cy,r,a1,a2,layer,wdt=0.1):
    p=lambda a:(cx+r*math.cos(math.radians(a)), cy+r*math.sin(math.radians(a)))
    s,m,e=p(a1),p((a1+a2)/2),p(a2)
    w(f'  (gr_arc (start {PX(s[0]):.4f} {PY(s[1]):.4f}) (mid {PX(m[0]):.4f} {PY(m[1]):.4f}) '
      f'(end {PX(e[0]):.4f} {PY(e[1]):.4f}) (stroke (width {wdt}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
def gtext(t,x,y,layer,size=1.0,thick=0.15,just=""):
    j=f' (justify {just})' if just else ''
    w(f'  (gr_text "{t}" (at {PX(x):.4f} {PY(y):.4f}) (layer "{layer}") (uuid "{U()}") '
      f'(effects (font (size {size} {size}) (thickness {thick})){j}))')

BWD,BHT,BRD = D.BW,D.BH,D.BR
cu=D.CUT; E="Edge.Cuts"
gline(BRD,0,cu["x1"],0,E); gline(cu["x2"],0,BWD-BRD,0,E)
gline(cu["x1"],0,cu["x1"],cu["depth"]-cu["r"],E)
gline(cu["x2"],cu["depth"]-cu["r"],cu["x2"],0,E)
gline(cu["x1"]+cu["r"],cu["depth"],cu["x2"]-cu["r"],cu["depth"],E)
garc(cu["x1"]+cu["r"],cu["depth"]-cu["r"],cu["r"],180,90,E)
garc(cu["x2"]-cu["r"],cu["depth"]-cu["r"],cu["r"],90,0,E)
gline(BWD,BRD,BWD,BHT-BRD,E); gline(BWD-BRD,BHT,BRD,BHT,E); gline(0,BHT-BRD,0,BRD,E)
garc(BWD-BRD,BRD,BRD,270,360,E); garc(BWD-BRD,BHT-BRD,BRD,0,90,E)
garc(BRD,BHT-BRD,BRD,90,180,E); garc(BRD,BRD,BRD,180,270,E)

# ------------------------------------------------------------- footprintler
LAYSET = {"smd":'"F.Cu" "F.Paste" "F.Mask"', "thru":'"*.Cu" "*.Mask"', "np":'"F&B.Cu" "*.Mask"'}
for c in D.C:
    pads,(bw,bh) = c["fp"](*c["args"])
    ox,oy = offset(c)
    w(f'  (footprint "T3RS:{c["ref"]}" (layer "F.Cu") (uuid "{U()}") '
      f'(at {PX(c["x"]+ox):.4f} {PY(c["y"]-oy):.4f}{" "+str(c["rot"]) if c["rot"] else ""})')
    w(f'    (descr "{c["desc"]}") (attr {"exclude_from_pos_files exclude_from_bom" if c["ref"].startswith("MH") else ("through_hole" if any(p[6]=="thru" for p in pads) else "smd")})')
    w(f'    (property "Reference" "{c["ref"]}" (at 0 {-bh/2-1.1:.2f} 0) (layer "F.SilkS") (uuid "{U()}") '
      f'(effects (font (size 0.8 0.8) (thickness 0.13))))')
    w(f'    (property "Value" "{c["val"]}" (at 0 {bh/2+1.1:.2f} 0) (layer "F.Fab") (uuid "{U()}") '
      f'(effects (font (size 0.7 0.7) (thickness 0.12))))')
    for (pn,px,py,pw,ph,shape,typ,drill) in pads:
        net = c["nets"].get(pn,"")
        ns = f' (net {NETI[net]} "{net}")' if net else ''
        if typ=="np":
            w(f'    (pad "" np_thru_hole circle (at {px:.3f} {py:.3f}) (size {pw:.2f} {ph:.2f}) '
              f'(drill {drill:.2f}) (layers {LAYSET["np"]}) (uuid "{U()}"))')
        elif typ=="thru":
            w(f'    (pad "{pn}" thru_hole {shape} (at {px:.3f} {py:.3f}) (size {pw:.2f} {ph:.2f}) '
              f'(drill {drill:.2f}) (layers {LAYSET["thru"]}){ns} (uuid "{U()}"))')
        else:
            rr=' (roundrect_rratio 0.25)' if shape=="roundrect" else ''
            w(f'    (pad "{pn}" smd {shape} (at {px:.3f} {py:.3f}) (size {pw:.2f} {ph:.2f}) '
              f'(layers {LAYSET["smd"]}){rr}{ns} (uuid "{U()}"))')
    # govde ipek + courtyard
    if not c["ref"].startswith("MH"):
        for lay,exp,wd in (("F.Fab",0.0,0.1),("F.CrtYd",0.25,0.05)):
            x1,y1,x2,y2 = -bw/2-exp,-bh/2-exp,bw/2+exp,bh/2+exp
            w(f'    (fp_rect (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) '
              f'(stroke (width {wd}) (type solid)) (fill none) (layer "{lay}") (uuid "{U()}"))')
    w('  )')

# ------------------------------------------------------- pad konumu (kart koord)
def _rot(px,py,deg):
    a=math.radians(deg)
    return (px*math.cos(a)+py*math.sin(a), -px*math.sin(a)+py*math.cos(a))

BYREF = {c["ref"]:c for c in D.C}
def pad(ref, pn):
    c=BYREF[ref]; pads,_=c["fp"](*c["args"])
    for p in pads:
        if p[0]==str(pn):
            dx,dy=_rot(p[1],p[2],c["rot"]); ox,oy=offset(c)
            return (c["x"]+ox+dx, c["y"]-oy-dy)
    raise KeyError(f"{ref}.{pn}")

def pad_box(c):
    pads,_=c["fp"](*c["args"])
    ox,oy=offset(c); xs=[];ys=[]
    for p in pads:
        dx,dy=_rot(p[1],p[2],c["rot"]); pw,ph=p[3],p[4]
        if c["rot"]%180: pw,ph=ph,pw
        xs+= [c["x"]+ox+dx-pw/2, c["x"]+ox+dx+pw/2]
        ys+= [c["y"]-oy-dy-ph/2, c["y"]-oy-dy+ph/2]
    return (min(xs),min(ys),max(xs),max(ys))

def check_placement(gap=0.3):
    probs=[]
    boxes=[(c["ref"],pad_box(c)) for c in D.C]
    for i in range(len(boxes)):
        for j in range(i+1,len(boxes)):
            r1,b1=boxes[i]; r2,b2=boxes[j]
            ox=min(b1[2],b2[2])-max(b1[0],b2[0]); oy=min(b1[3],b2[3])-max(b1[1],b2[1])
            if ox>-gap and oy>-gap:
                probs.append(f"CAKISMA {r1}<->{r2} ({ox:+.1f},{oy:+.1f})")
    for r,b in boxes:
        if b[0]<0.5 or b[1]<0.5 or b[2]>D.BW-0.5 or b[3]>D.BH-0.5:
            probs.append(f"KENAR {r} {tuple(round(v,1) for v in b)}")
        cu=D.CUT
        if b[0]<cu["x2"]+0.5 and b[2]>cu["x1"]-0.5 and b[1]<cu["depth"]+0.5:
            probs.append(f"KESIT {r} {tuple(round(v,1) for v in b)}")
    return probs

# ------------------------------------------------------------------ bakir alan
def zone(net, layers, poly, prio=0, name=""):
    ni=NETI.get(net,0)
    w(f'  (zone (net {ni}) (net_name "{net}") (layers {layers}) (uuid "{U()}")'
      f' (name "{name}") (hatch edge 0.5) (priority {prio})')
    w('    (connect_pads (clearance 0.25))')
    w('    (min_thickness 0.2) (filled_areas_thickness no)')
    w('    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4) (island_removal_mode 1) (island_area_min 5))')
    w('    (polygon (pts')
    w('      ' + ' '.join(f'(xy {PX(x):.3f} {PY(y):.3f})' for x,y in poly))
    w('    ))')
    w('  )')

BP = [(0,0),(D.CUT["x1"],0),(D.CUT["x1"],D.CUT["depth"]),(D.CUT["x2"],D.CUT["depth"]),
      (D.CUT["x2"],0),(BWD,0),(BWD,BHT),(0,BHT)]
zone("GND",'"In1.Cu"',BP,10,"GND_PLANE")            # In1 = tam GND duzlemi
zone("GND",'"F.Cu" "B.Cu"',BP,1,"GND_FILL")          # yuzeylerde GND dolgu
# In2 = guc duzlemi, bolunmus
# In2 = guc duzlemi, cakismasiz bolunmus
zone("VSYS",   '"In2.Cu"',[(0,0),(D.CUT["x1"],0),(D.CUT["x1"],19),(0,19)],20,"VSYS_PLANE")
zone("+3V3",   '"In2.Cu"',[(0,19),(36,19),(36,BHT),(0,BHT)],20,"3V3_PLANE_L")
zone("+5V",    '"In2.Cu"',[(D.CUT["x1"],14),(60,14),(60,BHT),(36,BHT),(36,19),(D.CUT["x1"],19)],20,"5V_PLANE")
zone("VBAT_SW",'"In2.Cu"',[(60,0),(BWD,0),(BWD,42),(60,42)],20,"VBATSW_PLANE")
zone("+3V3",   '"In2.Cu"',[(60,42),(BWD,42),(BWD,50),(60,50)],20,"3V3_PLANE_R")
zone("+5V",    '"In2.Cu"',[(60,50),(BWD,50),(BWD,BHT),(60,BHT)],20,"5V_PLANE_R")

# yuksek akimli dugumler: yol yerine yerel F.Cu bakir alani
zone("VBAT_F", '"F.Cu"',[(24.5,2.2),(27.8,2.2),(27.8,8.0),(24.5,8.0)],30,"VBAT_F_POUR")
zone("VBAT",   '"F.Cu"',[(30.3,2.2),(35.8,2.2),(35.8,6.2),(30.3,6.2)],30,"VBAT_POUR")
zone("VSYS",   '"F.Cu"',[(61.8,17.6),(64.8,17.6),(64.8,22.4),(61.8,22.4)],30,"VSYS_POUR")
zone("VBAT_SW",'"F.Cu"',[(67.2,17.6),(70.2,17.6),(70.2,21.2),(67.2,21.2)],30,"VBATSW_POUR")

# --------------------------------------------------------------------- yollar
TR=[]
def track(net, pts, layer="F.Cu", width=0.3):
    for a,b in zip(pts,pts[1:]): TR.append((net,a,b,layer,width))
def via(net, p, layers=('F.Cu','In2.Cu')):
    w(f'  (via (at {PX(p[0]):.4f} {PY(p[1]):.4f}) (size 0.8) (drill 0.4) '
      f'(layers "{layers[0]}" "{layers[1]}") (net {NETI[net]}) (uuid "{U()}"))')

W_PWR, W_MED, W_SIG = 2.0, 1.0, 0.3
# batarya -> sigorta -> ters polarite -> shunt   (hepsi y=5 hattinda)
track("VBAT_RAW",[pad("J2","1"), pad("F1","1")], "F.Cu", W_PWR)
track("VBAT_F",  [pad("F1","2"), pad("Q1","5")], "F.Cu", W_PWR)
track("VBAT",    [pad("Q1","1"), pad("Q1","3")], "F.Cu", W_MED)     # sadece source, gate haric
track("VBAT",    [pad("Q1","2"), pad("RS1","1")], "F.Cu", W_MED)
# shunt sonrasi ana ray -> In2 VSYS duzlemi
track("VSYS",    [pad("RS1","2"), (38.2,2.5)], "F.Cu", W_PWR)
# ana ray -> acil stop FET (kesitin ustunden, y=16.5)
track("VSYS",    [(38.0,16.5), (63.3,16.5), pad("Q2","8")], "F.Cu", W_PWR)
# estop cikisi -> In2 VBAT_SW duzlemi
track("VBAT_SW", [pad("Q2","2"), (71.0,19.365)], "F.Cu", W_PWR)
# 5V BEC -> In2 +5V duzlemi
track("SW5V",    [pad("U7","2"), (18.8,14.0), (18.8,17.5), pad("L1","1")], "F.Cu", 0.8)
track("+5V",     [pad("L1","2"), pad("C6","1")], "F.Cu", W_MED)
track("+5V",     [pad("C6","1"), (24.85,20.5), (38.0,20.5)], "F.Cu", W_MED)
# 3V3 LDO -> In2 +3V3 duzlemi
track("+3V3",    [pad("U6","5"), (35.3,47.5)], "F.Cu", W_MED)

for net,a,b,lay,wd in TR:
    if net not in NETI: continue
    w(f'  (segment (start {PX(a[0]):.4f} {PY(a[1]):.4f}) (end {PX(b[0]):.4f} {PY(b[1]):.4f}) '
      f'(width {wd}) (layer "{lay}") (net {NETI[net]}) (uuid "{U()}"))')

via("VSYS",(38.2,2.5)); via("VSYS",(38.0,16.5)); via("VBAT_SW",(71.0,19.365))
via("+5V",(38.0,20.5)); via("+3V3",(35.3,47.5))
# GND dikis vialari
for gx in range(6, 84, 8):
    for gy in range(4, 54, 8):
        if D.CUT["x1"]-2 < gx < D.CUT["x2"]+2 and gy < D.CUT["depth"]+2: continue
        if any(b[0]-0.6<gx<b[2]+0.6 and b[1]-0.6<gy<b[3]+0.6 for b in (pad_box(c) for c in D.C)): continue
        w(f'  (via (at {PX(gx):.4f} {PY(gy):.4f}) (size 0.8) (drill 0.4) '
          f'(layers "F.Cu" "B.Cu") (net {NETI["GND"]}) (uuid "{U()}"))')

# ------------------------------------------------------------------ ipek baski
S="F.SilkS"
gtext("T3-REDSTONE",3.0,53.5,S,2.2,0.35)
gtext("ROS2 ROBOT KONTROL KARTI",3.0,50.5,S,0.9,0.15)
gtext("T3 GEMSTONE O1",3.0,48.8,S,0.9,0.15)
gtext("2S LiPo 6.0-8.4V",6.0,10.5,S,1.0,0.18)
gtext("TERS BAGLAMA KORUMALI",6.0,9.0,S,0.7,0.12)
gtext("GEMSTONE GUC",19.0,20.0,S,0.8,0.13)
gtext("SERVO 1-8",30.5,42.5,S,0.9,0.15)
gtext("SERVO 9-16",30.5,34.5,S,0.9,0.15)
gtext("MOTOR A",71.0,22.5,S,0.9,0.15)
gtext("MOTOR B",71.0,10.5,S,0.9,0.15)
gtext("ENK A",60.0,55.2,S,0.8,0.13)
gtext("ENK B",73.0,55.2,S,0.8,0.13)
gtext("ANT",2.0,36.5,S,0.8,0.13)
gtext("USB",8.5,46.0,S,0.8,0.13)
gtext("KAMERA / DSI ERISIMI",43.0,16.5,S,1.0,0.16)
gtext("ACIL STOP",13.0,24.5,S,0.8,0.13)
gtext("BUMPER",60.5,21.0,S,0.8,0.13)
gtext("QWIIC I2C",56.0,49.0,S,0.7,0.12)
# uyarilar
gtext("!! DISI SOKET >=16mm  -  USB-A/RJ45 UZERINDEN GECER",8.5,45.5,"F.Fab",1.0,0.16)
gtext("PWM-0A/0B ve PWM-1A/1B AYNI PERIYODU PAYLASIR",43.0,26.0,"Dwgs.User",0.9,0.15)
# Gemstone'un yuksek konnektor bolgeleri
Dl="Dwgs.User"
for nm,x1,y1,x2,y2 in [("USB-A x3",68.0,20.0,85.0,52.0),("RJ45",60.0,0.0,85.0,18.0)]:
    for a,b in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:
        gline(a[0],a[1],b[0],b[1],Dl,0.2)
    gtext(f"{nm} h~13.5mm",(x1+x2)/2,(y1+y2)/2,Dl,0.9,0.14)
# pin1 isareti
gtext("1",D.J1_PIN1[0]-2.2,D.J1_PIN1[1],S,1.0,0.18)

w(')')
open("t3-redstone.kicad_pcb","w").write("\n".join(out)+"\n")

probs=check_placement()
print(f"komponent {len(D.C)}  net {len(NETI)}  satir {len(out)}")
print("YERLESIM:", "temiz" if not probs else f"{len(probs)} sorun")
for p in probs[:25]: print("  -",p)
