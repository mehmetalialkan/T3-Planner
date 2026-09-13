"""T3-Redstone board generator - cekirdek: katmanlar, stackup, footprint ureticiler."""
import math, uuid

def U(): return str(uuid.uuid4())

# ---------------------------------------------------------------- katmanlar
LAYERS = [(0,"F.Cu","signal"),(1,"In1.Cu","signal"),(2,"In2.Cu","signal"),(31,"B.Cu","signal"),
 (32,"B.Adhes","user"),(33,"F.Adhes","user"),(34,"B.Paste","user"),(35,"F.Paste","user"),
 (36,"B.SilkS","user"),(37,"F.SilkS","user"),(38,"B.Mask","user"),(39,"F.Mask","user"),
 (40,"Dwgs.User","user"),(41,"Cmts.User","user"),(42,"Eco1.User","user"),(43,"Eco2.User","user"),
 (44,"Edge.Cuts","user"),(45,"Margin","user"),(46,"B.CrtYd","user"),(47,"F.CrtYd","user"),
 (48,"B.Fab","user"),(49,"F.Fab","user")]

# KIRMIZI lehim maskesi + ENIG, 4 katman 1.6mm
STACKUP = '''    (stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Red") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0175))
      (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0175))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Red") (thickness 0.01))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )'''

# ------------------------------------------------------------ footprint uretici
# Her uretici (padname, x, y, w, h, sekil, tip, drill) listesi + govde (w,h) dondurur.

def sop(n, pitch, span, padw, padh, bodyw, bodyh, ep=None):
    """SOIC/TSSOP/VSSOP/SSOP. n=toplam pin (cift). span=pad merkezleri arasi mesafe."""
    pads=[]; per=n//2
    y0=-(per-1)*pitch/2
    for i in range(per):                       # sol kolon, yukaridan asagi
        pads.append((str(i+1), -span/2, y0+i*pitch, padw, padh, "roundrect","smd",0))
    for i in range(per):                       # sag kolon, asagidan yukari
        pads.append((str(per+i+1), span/2, y0+(per-1-i)*pitch, padw, padh, "roundrect","smd",0))
    if ep: pads.append(("EP",0,0,ep[0],ep[1],"rect","smd",0))
    return pads,(bodyw,bodyh)

def sot23(n, pitch=0.95, span=2.6, padw=1.0, padh=0.6):
    pads=[]
    if n==5: left=[1,2,3]; right=[5,4]; ry=[-pitch,pitch]
    else:    left=[1,2,3]; right=[6,5,4]; ry=[-pitch,0,pitch]
    for i,p in enumerate(left):
        pads.append((str(p), -span/2, (i-1)*pitch, padw, padh, "roundrect","smd",0))
    for i,p in enumerate(right):
        pads.append((str(p),  span/2, ry[i] if n==5 else (i-1)*pitch, padw, padh, "roundrect","smd",0))
    return pads,(2.9,1.6)

def chip(size="0805"):
    d={"0603":(0.9,0.95,1.6,0.85),"0805":(1.0,1.3,2.0,1.25),"1206":(1.1,1.8,3.2,1.7),
       "2512":(2.0,3.4,6.4,3.2),"5050":(2.6,3.2,5.0,5.0)}[size]
    padw,span,bw,bh=d
    return ([("1",-span/2,0,padw,bh*0.8,"roundrect","smd",0),
             ("2", span/2,0,padw,bh*0.8,"roundrect","smd",0)],(bw,bh))

def header(cols, rows, pitch=2.54, drill=1.0, pad=1.7):
    """THT pin header/soket. Pin1 sol-ust, cift sira icin 1=alt sira."""
    pads=[]
    for c in range(cols):
        for r in range(rows):
            n = c*rows + r + 1
            pads.append((str(n), c*pitch, -r*pitch, pad, pad,
                         "rect" if n==1 else "circle","thru",drill))
    w=(cols-1)*pitch+pad+1.0; h=(rows-1)*pitch+pad+1.0
    return pads,(w,h)

def terminal(n, pitch=5.08, drill=1.3, pad=2.4):
    pads=[(str(i+1), i*pitch, 0, pad, pad, "rect" if i==0 else "circle","thru",drill) for i in range(n)]
    return pads,((n-1)*pitch+pitch, 9.0)

def jst_xh(n, pitch=2.5, drill=0.9, pad=1.6):
    pads=[(str(i+1), i*pitch, 0, pad, pad, "rect" if i==0 else "circle","thru",drill) for i in range(n)]
    return pads,((n-1)*pitch+4.0, 6.0)

def jst_sh(n, pitch=1.0):
    pads=[(str(i+1),(i-(n-1)/2)*pitch, 0, 0.6, 1.55,"roundrect","smd",0) for i in range(n)]
    pads+= [("MP1",-(n*pitch/2+1.3),-1.8,1.2,1.8,"roundrect","smd",0),
            ("MP2", (n*pitch/2+1.3),-1.8,1.2,1.8,"roundrect","smd",0)]
    return pads,(n*pitch+3.6, 4.25)

def xt60():
    return ([("1",-3.9,0,3.5,3.5,"circle","thru",2.6),
             ("2", 3.9,0,3.5,3.5,"circle","thru",2.6)],(16.0,8.0))

def tact_smd():
    return ([("1",-3.25,-1.1,1.2,1.4,"roundrect","smd",0),("2",3.25,-1.1,1.2,1.4,"roundrect","smd",0),
             ("3",-3.25, 1.1,1.2,1.4,"roundrect","smd",0),("4",3.25, 1.1,1.2,1.4,"roundrect","smd",0)],(6.0,3.8))

def ufl():
    return ([("1",0,-1.5,1.0,1.05,"roundrect","smd",0),
             ("2",-1.55,1.1,1.4,1.0,"roundrect","smd",0),
             ("2",1.55,1.1,1.4,1.0,"roundrect","smd",0)],(3.0,3.0))

def usbc_16():
    """USB-C 16 pin yatay soket, basitlestirilmis (sadece USB2.0 hatlari)."""
    pads=[]
    names=["A1","A4","A5","A6","A7","A9","A12","B1","B4","B5","B6","B7","B9","B12"]
    xs=[-3.2,-2.4,-1.6,-0.8,0.0,0.8,1.6,-3.2+0.4,-2.4+0.4,-1.6+0.4,-0.8+0.4,0.4,1.2,2.0]
    for i,(nm,x) in enumerate(zip(names,xs)):
        pads.append((nm, x, -0.9 if i<7 else 0.9, 0.3, 1.15,"roundrect","smd",0))
    for i,x in enumerate((-4.32,4.32)):
        pads.append((f"S{i+1}", x, 0, 2.1, 3.4,"roundrect","smd",0))
    return pads,(9.0,7.5)

def wroom1u():
    """ESP32-S3-WROOM-1U (18.0 x 19.2 mm), 1.27mm kastelasyon.
    !! Pad numaralari veri sayfasindan; uretime gitmeden resmi kutuphane
       footprint'i ile karsilastir."""
    pads=[]; P=1.27; BW,BH=18.0,19.2
    y0=-(15-1)*P/2
    for i in range(15):                                   # 1..15 sol kenar
        pads.append((str(i+1), -BW/2+0.45, y0+i*P, 1.5, 0.9,"roundrect","smd",0))
    x0=-(9-1)*P/2
    for i in range(9):                                    # 16..24 alt kenar
        pads.append((str(16+i), x0+i*P, BH/2-0.45, 0.9, 1.5,"roundrect","smd",0))
    for i in range(15):                                   # 25..39 sag kenar
        pads.append((str(25+i), BW/2-0.45, y0+(14-i)*P, 1.5, 0.9,"roundrect","smd",0))
    pads.append(("40", -BW/2+0.45, y0-P, 1.5, 0.9,"roundrect","smd",0))
    pads.append(("41", 0, 0, 5.3, 5.3,"rect","smd",0))    # termal pad
    return pads,(BW,BH)

def mount(d=2.75):
    return ([("", 0,0,d,d,"circle","np",d)],(d+1.5,d+1.5))
