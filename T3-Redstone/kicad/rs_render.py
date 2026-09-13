"""Board verisinden SVG onizleme + yol/pad DRC."""
import math, sys
sys.path.insert(0,'.')
import rs_emit as E, rs_design as D
from rs_lib import *

# ---------------------------------------------------------------- basit DRC
def seg_pt_dist(a,b,p):
    ax,ay=a; bx,by=b; px,py=p
    dx,dy=bx-ax,by-ay
    if dx==dy==0: return math.hypot(px-ax,py-ay)
    t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def seg_rect_dist(a,b,cx,cy,hw,hh,n=24):
    """Segment ile eksen-hizali dikdortgen arasi mesafe (ornekleyerek)."""
    best=1e9
    for i in range(n+1):
        t=i/n
        px=a[0]+(b[0]-a[0])*t; py=a[1]+(b[1]-a[1])*t
        ddx=max(abs(px-cx)-hw,0.0); ddy=max(abs(py-cy)-hh,0.0)
        best=min(best, math.hypot(ddx,ddy))
    return best

def drc():
    probs=[]
    pads=[]
    for c in D.C:
        pl,_=c["fp"](*c["args"]); ox,oy=E.offset(c)
        for p in pl:
            dx,dy=E._rot(p[1],p[2],c["rot"]); pw,ph=p[3],p[4]
            if c["rot"]%180: pw,ph=ph,pw
            pads.append((c["ref"],p[0],c["nets"].get(p[0],""),
                         c["x"]+ox+dx, c["y"]-oy-dy, pw/2, ph/2))
    for net,a,b,lay,wd in E.TR:
        if not net or net not in E.NETI: continue
        for ref,pn,pnet,px,py,phw,phh in pads:
            if pnet==net: continue
            d=seg_rect_dist(a,b,px,py,phw,phh) - wd/2
            if d < 0.2:
                probs.append(f"{net} yolu <-> {ref}.{pn}({pnet or 'bos'})  bosluk {d:+.2f}mm")
    # yol-yol
    for i in range(len(E.TR)):
        for j in range(i+1,len(E.TR)):
            n1,a1,b1,l1,w1=E.TR[i]; n2,a2,b2,l2,w2=E.TR[j]
            if n1==n2 or l1!=l2: continue
            d=min(seg_pt_dist(a1,b1,a2),seg_pt_dist(a1,b1,b2),
                  seg_pt_dist(a2,b2,a1),seg_pt_dist(a2,b2,b1)) - (w1+w2)/2
            if d < 0.2: probs.append(f"{n1} <-> {n2} yollari  bosluk {d:+.2f}mm")
    return probs

# ---------------------------------------------------------------- SVG cizim
SC=10                       # px/mm
def sx(x): return x*SC
def sy(y): return (D.BH-y)*SC

def render(path):
    W,H=D.BW*SC,D.BH*SC
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append('<rect width="100%" height="100%" fill="#1a1d21"/>')
    cu=D.CUT
    o.append(f'<path d="M {sx(3)} {sy(0)} L {sx(cu["x1"])} {sy(0)} L {sx(cu["x1"])} {sy(cu["depth"])} '
             f'L {sx(cu["x2"])} {sy(cu["depth"])} L {sx(cu["x2"])} {sy(0)} L {sx(D.BW-3)} {sy(0)} '
             f'A {3*SC} {3*SC} 0 0 0 {sx(D.BW)} {sy(3)} L {sx(D.BW)} {sy(D.BH-3)} '
             f'A {3*SC} {3*SC} 0 0 0 {sx(D.BW-3)} {sy(D.BH)} L {sx(3)} {sy(D.BH)} '
             f'A {3*SC} {3*SC} 0 0 0 {sx(0)} {sy(D.BH-3)} L {sx(0)} {sy(3)} '
             f'A {3*SC} {3*SC} 0 0 0 {sx(3)} {sy(0)} Z" fill="#8f1d1d" stroke="#d4d4d4" stroke-width="1.5"/>')
    # bolge etiketleri
    for tx,ty,t in [(17,32,"ESP32-S3"),(22,9,"GUC"),(48,40,"SERVO"),(70,31,"MOTOR"),
                    (70,49,"ENKODER"),(48.5,7,"KAMERA / DSI")]:
        o.append(f'<text x="{sx(tx)}" y="{sy(ty)}" fill="#ffffff20" font-size="26" '
                 f'font-family="sans-serif" text-anchor="middle" font-weight="bold">{t}</text>')
    # yollar
    for net,a,b,lay,wd in E.TR:
        if not net or net not in E.NETI: continue
        o.append(f'<line x1="{sx(a[0])}" y1="{sy(a[1])}" x2="{sx(b[0])}" y2="{sy(b[1])}" '
                 f'stroke="#e8b423" stroke-width="{wd*SC}" stroke-linecap="round" opacity="0.9"/>')
    # padler + govde
    for c in D.C:
        bx=E.pad_box(c)
        if not c["ref"].startswith("MH"):
            o.append(f'<rect x="{sx(bx[0])}" y="{sy(bx[3])}" width="{(bx[2]-bx[0])*SC}" '
                     f'height="{(bx[3]-bx[1])*SC}" fill="none" stroke="#ffffff" stroke-width="0.7" opacity="0.55"/>')
        pl,_=c["fp"](*c["args"]); ox,oy=E.offset(c)
        for p in pl:
            dx,dy=E._rot(p[1],p[2],c["rot"]); pw,ph=p[3],p[4]
            if c["rot"]%180: pw,ph=ph,pw
            X,Y=c["x"]+ox+dx, c["y"]-oy-dy
            col = "#2b2b2b" if p[6]=="np" else "#e8d9a0"
            if p[6]=="thru":
                o.append(f'<circle cx="{sx(X)}" cy="{sy(Y)}" r="{max(pw,ph)/2*SC}" fill="{col}"/>'
                         f'<circle cx="{sx(X)}" cy="{sy(Y)}" r="{p[7]/2*SC}" fill="#1a1d21"/>')
            elif p[6]=="np":
                o.append(f'<circle cx="{sx(X)}" cy="{sy(Y)}" r="{pw/2*SC}" fill="#1a1d21" stroke="#ccc" stroke-width="1"/>')
            else:
                o.append(f'<rect x="{sx(X-pw/2)}" y="{sy(Y+ph/2)}" width="{pw*SC}" height="{ph*SC}" '
                         f'rx="{min(pw,ph)*0.2*SC}" fill="{col}"/>')
        ty = bx[3]+0.9
        o.append(f'<text x="{sx((bx[0]+bx[2])/2)}" y="{sy(ty)}" fill="#ffffff" font-size="8.5" '
                 f'font-family="monospace" text-anchor="middle">{c["ref"]}</text>')
    # ipek baski basliklari
    for t,x,y,sz in [("T3-REDSTONE",3,53.5,22),("ROS2 ROBOT KONTROL KARTI",3,50.3,9),
                     ("T3 GEMSTONE O1",3,48.6,9),("2S LiPo 6.0-8.4V",6,1.5,10)]:
        o.append(f'<text x="{sx(x)}" y="{sy(y)}" fill="#ffffff" font-size="{sz}" '
                 f'font-family="sans-serif" font-weight="bold">{t}</text>')
    o.append('</svg>')
    open(path,"w").write("\n".join(o))

if __name__=="__main__":
    p=drc()
    print("YOL DRC:", "temiz" if not p else f"{len(p)} sorun")
    for x in p[:20]: print("  -",x)
    render("../mekanik/t3-redstone-preview.svg")
    print("onizleme: mekanik/t3-redstone-preview.svg")
