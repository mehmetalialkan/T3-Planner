#!/usr/bin/env python3
"""T3-Redstone - sinyal yonlendirme + GND dokumleri + dolgu + DRC.

    python3 rs_build.py        # once: yerlesim + guc
    python3 rs_route.py        # Freerouting -> SES -> karta

Gerekenler: KiCad 7 (pcbnew Python), Java 25+, Freerouting 2.4.x executable jar.
    FREEROUTING_JAR=/yol/freerouting-2.4.1-executable.jar  JAVA=/yol/java

Kilitli (locked) yollar rs_build.py'nin guc yollaridir ve korunur; kilitsiz her
yol bu betik her calistiginda silinip yeniden cizilir.
"""
import math
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_design as D          # noqa: E402

PCB = os.path.join(HERE, "t3-redstone.kicad_pcb")
WORK = os.environ.get("RS_WORK", os.path.join(HERE, "build"))
DSN = os.path.join(WORK, "t3-redstone.dsn")
SES = os.path.join(WORK, "t3-redstone.ses")
DRC = os.path.join(WORK, "drc.rpt")
JAR = os.environ.get("FREEROUTING_JAR", os.path.join(HERE, "..", "tools", "freerouting-2.4.1-executable.jar"))
JAVA = os.environ.get("JAVA", "java")
PASSES = os.environ.get("FR_PASSES", "300")
MM = pcbnew.FromMM
ORGX, ORGY = 30.0, 30.0


def V(x, y):
    return pcbnew.VECTOR2I(MM(ORGX + x), MM(ORGY + D.BH - y))


# ---------------------------------------------------------------- s-ifade okuyucu
def sexp(text):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    st = [[]]
    for t in tok:
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


# ----------------------------------------------------------------------- hazirlik
os.makedirs(WORK, exist_ok=True)
board = pcbnew.LoadBoard(PCB)
# Remove() KiCad 7'nin SWIG katmanini bozuyor (sonraki Zones()/GetTracks() cagrilari
# SwigPyObject donuyor); Delete() guvenli.
for t in [t for t in board.GetTracks() if not t.IsLocked()]:
    board.Delete(t)
for z in [z for z in board.Zones() if z.GetZoneName() in ("GND_F", "GND_B")]:
    board.Delete(z)

PRE = os.path.join(WORK, "pre-route.kicad_pcb")

def freeroute(src, dsn, ses, passes, logname, optimize=True):
    """src kartini DSN'e aktar, Freerouting'i calistir. F.Cu guc dokumleri DSN'e
    cerceveleriyle degil DOLGU sekilleriyle gider: cerceve komsu pinlerin ustunden
    gecebilir (dolgu motoru orada bosluk birakir), Freerouting ise cerceveyi kati
    bakir sanar. GND yuzey dokumleri DSN'e girmez (her yeri kaplar)."""
    b_ = pcbnew.LoadBoard(src)
    for z in [z for z in b_.Zones() if z.GetZoneName() in ("GND_F", "GND_B")]:
        b_.Delete(z)
    pcbnew.ZONE_FILLER(b_).Fill(b_.Zones())
    for z in b_.Zones():
        if z.GetZoneName().startswith("F_"):
            fill = z.GetFilledPolysList(pcbnew.F_Cu)
            shape = pcbnew.SHAPE_POLY_SET()
            for i in range(fill.OutlineCount()):
                shape.AddOutline(fill.Outline(i))
            if shape.OutlineCount():
                z.Outline().RemoveAllContours()
                for i in range(shape.OutlineCount()):
                    z.Outline().AddOutline(shape.Outline(i))
    assert pcbnew.ExportSpecctraDSN(b_, dsn), "DSN yazilamadi"
    if os.path.exists(ses):
        os.remove(ses)
    cmd = [JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-mp", passes,
           "--gui.enabled=false", "--usage_and_diagnostic_data.disable_analytics=true"]
    if not optimize:
        cmd.append("--router.optimizer.enabled=false")
    print("freerouting:", " ".join(cmd[2:]), flush=True)
    with open(os.path.join(WORK, logname), "w") as logf:
        subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)
    if not os.path.exists(ses):
        if logname == "freerouting.log":
            sys.exit(f"Freerouting SES uretmedi - build/{logname}")
        print(f"UYARI: Freerouting SES uretmedi - build/{logname}")




# ------------------------------------------------------------------- SES -> kart
def seg_dist(p, a, b):
    ax, ay, bx, by = a.x, a.y, b.x, b.y
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p.x - ax) * dx + (p.y - ay) * dy) / (dx * dx + dy * dy)))
    return ((p.x - ax - t * dx) ** 2 + (p.y - ay - t * dy) ** 2) ** 0.5


def import_ses(path):
    """SES'teki yol/via'lari karta ekle; kartta zaten olanlari (ayni net, ayni katman,
    mevcut bir yolun ustunde kalan parca / ayni yerdeki via) atla."""
    ses = sexp(open(path).read())
    routes = find(ses, "routes")[0]
    res = find(routes, "resolution")[0]           # (resolution um 10)
    scale = 1.0 / float(res[2])                    # birim -> um
    padstacks = {}
    for ps in find(find(routes, "library_out")[0], "padstack") if find(routes, "library_out") else []:
        m = re.search(r"_(\d+):(\d+)_um", ps[1])
        padstacks[ps[1]] = (int(m.group(1)), int(m.group(2))) if m else (600, 300)
    segs = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            segs.setdefault((t.GetNetname(), t.GetLayer()), []).append((t.GetStart(), t.GetEnd()))
    vias = [o.GetPosition() for o in board.GetTracks() if o.GetClass() == "PCB_VIA"]

    def pt(x, y):
        """SES (um * res, Y yukari, sayfa) -> KiCad nm"""
        return pcbnew.VECTOR2I(int(round(float(x) * scale * 1000)), int(round(-float(y) * scale * 1000)))

    def covered(name, layer, a, b):
        for s0, s1 in segs.get((name, layer), ()):
            if seg_dist(a, s0, s1) < 1000 and seg_dist(b, s0, s1) < 1000:
                return True
        return False

    n_wire = n_via = 0
    for net in find(find(routes, "network_out")[0], "net"):
        name = net[1]
        ni = board.FindNet(name)
        if ni is None:
            print("UYARI: SES'te bilinmeyen net", name)
            continue
        for w in find(net, "wire"):
            if find(w, "type") and find(w, "type")[0][1] in ("fix", "protect"):
                continue
            path_ = find(w, "path")[0]
            layer = board.GetLayerID(path_[1])
            width = int(round(float(path_[2]) * scale * 1000))
            pts = [pt(path_[i], path_[i + 1]) for i in range(3, len(path_) - 1, 2)]
            for a, b in zip(pts, pts[1:]):
                if covered(name, layer, a, b):
                    continue
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a)
                t.SetEnd(b)
                t.SetWidth(width)
                t.SetLayer(layer)
                t.SetNet(ni)
                board.Add(t)
                segs.setdefault((name, layer), []).append((a, b))
                n_wire += 1
        for v in find(net, "via"):
            if find(v, "type") and find(v, "type")[0][1] in ("fix", "protect"):
                continue
            dia, drill = padstacks.get(v[1], (600, 300))
            pos = pt(v[2], v[3])
            if any(abs(o.x - pos.x) < 50000 and abs(o.y - pos.y) < 50000 for o in vias):
                continue
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pos)
            via.SetWidth(int(dia * 1000))
            via.SetDrill(int(drill * 1000))
            via.SetNet(ni)
            board.Add(via)
            vias.append(pos)
            n_via += 1
    print(f"SES: {n_wire} yol parcasi, {n_via} via eklendi")



# ---------------------------------------------------------------- engel denetimi
OUTLINE = [(0, 0), (D.CUT["x1"], 0), (D.CUT["x1"], D.CUT["depth"]), (D.CUT["x2"], D.CUT["depth"]),
           (D.CUT["x2"], 0), (D.BW, 0), (D.BW, D.BH), (0, D.BH)]
gnd = board.FindNet("GND")
VIA_D, VIA_DR, GAP = 0.5, 0.25, 0.2
COPPER = (pcbnew.F_Cu, pcbnew.B_Cu)


def board_xy(p):
    return (pcbnew.ToMM(p.x) - ORGX, D.BH - (pcbnew.ToMM(p.y) - ORGY))


def on_board(p, margin=0.6):
    x, y = board_xy(p)
    if not (margin < x < D.BW - margin and margin < y < D.BH - margin):
        return False
    c = D.CUT
    if c["x1"] - margin < x < c["x2"] + margin and y < c["depth"] + margin:
        return False
    for cx, cy in ((3, 3), (3, D.BH - 3), (D.BW - 3, 3), (D.BW - 3, D.BH - 3)):
        if (x < 3 or x > D.BW - 3) and (y < 3 or y > D.BH - 3) and \
                ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 > 3 - margin:
            return False
    return True


def point_clear(p, r, net, layers=COPPER, courtyard=False, own_pad=None):
    """p etrafinda r yaricapli bakir, 'net' disindaki her seyden GAP uzakta mi?"""
    # SWIG her cagrida yeni sarmalayici dondurur: 'is' hic eslesmez, UUID karsilastir
    own = own_pad.m_Uuid.AsString() if own_pad is not None else None
    for fp in board.GetFootprints():
        for q in fp.Pads():
            if own is not None and q.m_Uuid.AsString() == own:
                continue
            if not any(q.IsOnLayer(lay) for lay in layers) and q.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            bb = q.GetBoundingBox()
            m = r + (MM(GAP) if q.GetNetname() != net else MM(0.05))
            if bb.GetLeft() - m < p.x < bb.GetRight() + m and bb.GetTop() - m < p.y < bb.GetBottom() + m:
                return False
        if courtyard:
            for g in fp.GraphicalItems():
                if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                    bb = g.GetBoundingBox()
                    if bb.GetLeft() < p.x < bb.GetRight() and bb.GetTop() < p.y < bb.GetBottom():
                        return False
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            d = ((t.GetPosition().x - p.x) ** 2 + (t.GetPosition().y - p.y) ** 2) ** 0.5
            if d < t.GetWidth() / 2 + r + (MM(GAP) if t.GetNetname() != net else MM(0.1)):
                return False
        elif t.GetLayer() in layers and t.GetNetname() != net:
            if seg_dist(p, t.GetStart(), t.GetEnd()) < t.GetWidth() / 2 + r + MM(GAP):
                return False
    for z in board.Zones():
        if z.GetNetname() != net and z.GetZoneName() not in ("GND_F", "GND_B") and \
                any(z.IsOnLayer(lay) for lay in layers):
            if z.Outline().Collide(p, int(r + MM(GAP))):
                return False
    return True


def in_plane(net, p, margin=0.5):
    """Via buradan inerse 'net' duzlemine (In1 GND / In2 bolgesi) baglanir mi?"""
    if net == "GND":
        return True
    x, y = board_xy(p)
    for nm, poly in D.IN2_SPLIT:
        if nm != net:
            continue
        inside = False
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside and all(seg_dist(pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6)),
                                   pcbnew.VECTOR2I(int(x1 * 1e6), int(y1 * 1e6)),
                                   pcbnew.VECTOR2I(int(x2 * 1e6), int(y2 * 1e6))) > margin * 1e6
                          for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1])):
            return True
    return False


def add_via(net, p, d=VIA_D, dr=VIA_DR):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(p)
    v.SetWidth(MM(d))
    v.SetDrill(MM(dr))
    v.SetNet(board.FindNet(net))
    board.Add(v)


# ---------------------------------------------------- guc pinleri icin fanout onarimi
PLANE_NETS = {"GND"} | {nm for nm, _ in D.IN2_SPLIT}


def fanout(q, w=0.25, via_d=VIA_D, via_dr=VIA_DR):
    """SMD pedden kisa bir yol + via ile ilgili duzleme in. Basarili ise True."""
    net = q.GetNetname()
    c = q.GetPosition()
    bb = q.GetBoundingBox()
    base = max(bb.GetWidth(), bb.GetHeight()) / 2
    layer = pcbnew.F_Cu if q.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    for step in range(0, 14):
        dist = base + MM(0.45 + 0.2 * step)
        for k in range(24):
            ang = 2 * math.pi * k / 24
            p = pcbnew.VECTOR2I(int(c.x + dist * math.cos(ang)), int(c.y + dist * math.sin(ang)))
            if not (on_board(p) and in_plane(net, p) and point_clear(p, MM(via_d / 2), net)):
                continue
            ok = True
            for i in range(1, 12):                       # yol boyunca ornekle
                t = i / 12
                s_ = pcbnew.VECTOR2I(int(c.x + (p.x - c.x) * t), int(c.y + (p.y - c.y) * t))
                if not point_clear(s_, MM(w / 2), net, layers=(layer,), own_pad=q):
                    ok = False
                    break
            if not ok:
                continue
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(c)
            tr.SetEnd(p)
            tr.SetWidth(MM(w))
            tr.SetLayer(layer)
            tr.SetNet(q.GetNet())
            board.Add(tr)
            add_via(net, p, via_d, via_dr)
            return True
    return False


def attached(q):
    bb = q.GetBoundingBox()
    bb.Inflate(MM(0.02))
    for t in board.GetTracks():
        if t.GetNetname() != q.GetNetname():
            continue
        if t.GetClass() == "PCB_VIA":
            if bb.Contains(t.GetPosition()):
                return True
        elif q.IsOnLayer(t.GetLayer()) and (bb.Contains(t.GetStart()) or bb.Contains(t.GetEnd())):
            return True
    for z in board.Zones():
        if z.GetZoneName().startswith("F_") and z.GetNetname() == q.GetNetname() and \
                z.Outline().Collide(q.GetPosition()):
            return True
    return False


# ------------------------------------------- yonlendirme ONCESI pasiflerin fanout'u
# Freerouting duzlem netlerinin fanout'unu her calismada farkli pinlerde atliyor ve
# sinyaller sonra o pinin etrafini kapatiyor. Pasiflerin (R/C/D/L/RN) guc pinleri bos
# kartta duzleme indirilir; bu yol/via'lar Freerouting'e sabit gider, sonra kilitleri
# acilir (bir sonraki calismada silinip yeniden uretilsinler).
PASSIVE = re.compile(r"(R|C|D|L|RN)\d+$")
prefan = []
for fp in board.GetFootprints():
    if not PASSIVE.match(fp.GetReference()):
        continue
    for q in fp.Pads():
        if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and q.GetNetname() in PLANE_NETS and \
                q.GetNetname() and not attached(q):
            before = {t.m_Uuid.AsString() for t in board.GetTracks()}
            if fanout(q) or fanout(q, via_d=0.45, via_dr=0.2):
                for t in [t for t in board.GetTracks() if t.m_Uuid.AsString() not in before]:
                    t.SetLocked(True)
                    prefan.append((t.GetClass(), t.GetPosition().x, t.GetPosition().y,
                                   t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y))
print(f"yonlendirme oncesi fanout: {sum(1 for p_ in prefan if p_[0] == 'PCB_VIA')} via")
pcbnew.SaveBoard(PRE, board)

if "--no-route" not in sys.argv:
    freeroute(PRE, DSN, SES, PASSES, "freerouting.log")

board = pcbnew.LoadBoard(PRE)
gnd = board.FindNet("GND")
import_ses(SES)
# Freerouting ince pinlerde yolu 0.1 mm'nin altina indirebiliyor (uretilebilirlik)
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetWidth() < MM(0.1):
        t.SetWidth(MM(0.1))


def unlock_prefan():
    keys = set(prefan)
    for t in board.GetTracks():
        if (t.GetClass(), t.GetPosition().x, t.GetPosition().y, t.GetStart().x, t.GetStart().y,
                t.GetEnd().x, t.GetEnd().y) in keys:
            t.SetLocked(False)


n_fan = n_fail = 0
for fp in board.GetFootprints():
    for q in fp.Pads():
        if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and q.GetNetname() in PLANE_NETS and not attached(q):
            if fanout(q) or fanout(q, via_d=0.45, via_dr=0.2):
                n_fan += 1
            else:
                n_fail += 1
                print(f"  fanout yapilamadi: {fp.GetReference()}.{q.GetNumber()} [{q.GetNetname()}]")
print(f"guc pini fanout: {n_fan} (basarisiz {n_fail})")

# ------------------------------------------------------------- GND dikis vialari
n_stitch = 0
y = 1.6
while y < D.BH - 1.2:
    x = 1.6
    while x < D.BW - 1.2:
        p = V(x, y)
        if on_board(p, 0.9) and point_clear(p, MM(VIA_D / 2), "GND", courtyard=True):
            add_via("GND", p)
            n_stitch += 1
        x += 2.0
    y += 2.0
print(f"GND dikis viasi: {n_stitch}")

# ------------------------------------------------------------- GND yuzey dokumleri
for lay, name in ((pcbnew.F_Cu, "GND_F"), (pcbnew.B_Cu, "GND_B")):
    z = pcbnew.ZONE(board)
    z.SetLayer(lay)
    z.SetNet(gnd)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in OUTLINE:
        v = V(x, y)
        ol.Append(v.x, v.y)
    z.SetAssignedPriority(0)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD dogrudan, THT termal
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name)
    board.Add(z)


# --------------------------------------------------------- dolgu + DRC + onarim dongusu
def drc():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.WriteDRCReport(board, DRC, pcbnew.EDA_UNITS_MILLIMETRES, True)
    return open(DRC).read()


def find_pad(ref, num):
    fp = board.FindFootprintByReference(ref)
    return [q for q in fp.Pads() if q.GetNumber() == num] if fp else []


def group_of(net, seed_pts, seed_pads):
    """Ayni netin birbirine geometrik olarak degen yol/via/pedlerini topla."""
    items = [t for t in board.GetTracks() if t.GetNetname() == net]
    allpads = [q for fp in board.GetFootprints() for q in fp.Pads() if q.GetNetname() == net]
    tol = MM(0.01)

    def is_via(t):
        return t.GetClass() == "PCB_VIA"

    def pad_hit(q, p, r=0):
        bb = q.GetBoundingBox()
        bb.Inflate(int(r))
        return bb.Contains(p)

    def track_touch(t, u):
        if is_via(t) and is_via(u):
            return ((t.GetPosition().x - u.GetPosition().x) ** 2 +
                    (t.GetPosition().y - u.GetPosition().y) ** 2) ** 0.5 < (t.GetWidth() + u.GetWidth()) / 2
        if is_via(u):
            t, u = u, t
        if is_via(t):
            return seg_dist(t.GetPosition(), u.GetStart(), u.GetEnd()) <= (t.GetWidth() + u.GetWidth()) / 2
        if t.GetLayer() != u.GetLayer():
            return False
        w = (t.GetWidth() + u.GetWidth()) / 2 + tol
        return min(seg_dist(t.GetStart(), u.GetStart(), u.GetEnd()), seg_dist(t.GetEnd(), u.GetStart(), u.GetEnd()),
                   seg_dist(u.GetStart(), t.GetStart(), t.GetEnd()), seg_dist(u.GetEnd(), t.GetStart(), t.GetEnd())) <= w

    def pad_touch(q, t):
        if is_via(t):
            return pad_hit(q, t.GetPosition())
        if not q.IsOnLayer(t.GetLayer()):
            return False
        return pad_hit(q, t.GetStart()) or pad_hit(q, t.GetEnd()) or \
            seg_dist(q.GetPosition(), t.GetStart(), t.GetEnd()) <= t.GetWidth() / 2

    tracks, pads = [], list(seed_pads)
    for t in items:                                    # tohum noktasina degen yollar
        for p in seed_pts:
            ok = pad_hit_any = False
            if is_via(t):
                ok = ((t.GetPosition().x - p.x) ** 2 + (t.GetPosition().y - p.y) ** 2) ** 0.5 <= t.GetWidth() / 2 + tol
            else:
                ok = seg_dist(p, t.GetStart(), t.GetEnd()) <= t.GetWidth() / 2 + tol
            if ok and t not in tracks:
                tracks.append(t)
    grew = True
    while grew:
        grew = False
        for t in items:
            if t in tracks:
                continue
            if any(track_touch(t, u) for u in tracks) or any(pad_touch(q, t) for q in pads):
                tracks.append(t)
                grew = True
        for q in allpads:
            if q in pads:
                continue
            if any(pad_touch(q, t) for t in tracks):
                pads.append(q)
                grew = True
    return tracks, pads


def via_on_group(net, tracks, via_d=VIA_D, via_dr=VIA_DR):
    """Grubun yollarindan birinin ustune, duzleme inen bir via koy."""
    for t in tracks:
        if t.GetClass() == "PCB_VIA":
            continue
        a_, b_ = t.GetStart(), t.GetEnd()
        n = max(1, int(((b_.x - a_.x) ** 2 + (b_.y - a_.y) ** 2) ** 0.5 / MM(0.2)))
        for i in range(n + 1):
            p = pcbnew.VECTOR2I(int(a_.x + (b_.x - a_.x) * i / n), int(a_.y + (b_.y - a_.y) * i / n))
            if on_board(p) and in_plane(net, p) and point_clear(p, MM(via_d / 2), net):
                add_via(net, p, via_d, via_dr)
                return True
    return False


def repair_group(net, pos, pad=None):
    tracks, pads = group_of(net, [pos], [pad] if pad else [])
    for t in tracks:                                   # zaten duzleme inen via var mi?
        if t.GetClass() == "PCB_VIA" and in_plane(net, t.GetPosition(), 0.3):
            return False
    smd = [q for q in pads if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    # once normal via (0.5/0.25), olmazsa kucuk via (0.45/0.2 - JLC 4 katmanda standart)
    for d, dr in ((VIA_D, VIA_DR), (0.45, 0.2)):
        if via_on_group(net, tracks, d, dr) or any(fanout(q, via_d=d, via_dr=dr) for q in smd):
            return True
    return False


def _lerp(a, b, t):
    return pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * t), int(a.y + (b.y - a.y) * t))


def _dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def _proj(p, a, b):
    dx, dy = b.x - a.x, b.y - a.y
    if dx == dy == 0:
        return a
    t = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy)))
    return _lerp(a, b, t)


def copper_clear(p, r, net, layers):
    """p etrafinda r yaricapli bakir baska netlerden GAP uzakta mi? (ayni net serbest)"""
    if not on_board(p):
        return False
    gap = MM(GAP)
    for fp in board.GetFootprints():
        for q in fp.Pads():
            if q.GetNetname() == net and q.GetNetname():
                continue
            if any(q.IsOnLayer(lay) for lay in layers) or q.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                if q.HitTest(p, int(r + gap)):
                    return False
    for t in board.GetTracks():
        if t.GetNetname() == net:
            continue
        if t.GetClass() == "PCB_VIA":
            if _dist(t.GetPosition(), p) < t.GetWidth() / 2 + r + gap:
                return False
        elif t.GetLayer() in layers and seg_dist(p, t.GetStart(), t.GetEnd()) < t.GetWidth() / 2 + r + gap:
            return False
    for z in board.Zones():
        if z.GetNetname() != net and z.GetZoneName() not in ("GND_F", "GND_B") and \
                any(z.IsOnLayer(lay) for lay in layers) and z.Outline().Collide(p, int(r + gap)):
            return False
    return True


def _anchors(tracks, pads):
    """(katman, a, b, yari_genislik) - via iki katmanda da nokta."""
    out = []
    for t in tracks:
        if t.GetClass() == "PCB_VIA":
            out += [(lay, t.GetPosition(), t.GetPosition(), t.GetWidth() / 2) for lay in COPPER]
        else:
            out.append((t.GetLayer(), t.GetStart(), t.GetEnd(), t.GetWidth() / 2))
    for q in pads:
        out += [(lay, q.GetPosition(), q.GetPosition(), 0) for lay in COPPER if q.IsOnLayer(lay)]
    return out


def join_groups(net, a_pos, a_pad, b_pos, b_pad, max_bridge=2.0):
    """Ayni netin iki kopuk parcasini bagla: farkli katmanda ust uste geliyorlarsa
    kesisime via, ayni katmanda yakinsa kisa duz yol."""
    ta, pa = group_of(net, [a_pos], [a_pad] if a_pad else [])
    tb, pb = group_of(net, [b_pos], [b_pad] if b_pad else [])
    def uid(o):
        return o.m_Uuid.AsString()
    if not (ta or pa) or not (tb or pb) or {uid(o) for o in ta + pa} & {uid(o) for o in tb + pb}:
        return False
    A, B = _anchors(ta, pa), _anchors(tb, pb)
    w = MM(0.25 if net in PLANE_NETS else 0.15)
    best = None                                       # (maliyet, tur, katman, p, q)
    for la, a1, a2, wa in A:
        n = max(1, int(_dist(a1, a2) / MM(0.05)))
        for lb, b1, b2, wb in B:
            for i in range(n + 1):
                p = _lerp(a1, a2, i / n)
                q = _proj(p, b1, b2)
                d = _dist(p, q)
                if la != lb and d < MM(0.05):
                    c = (0, "via", None, p, q)
                elif la == lb and d < MM(max_bridge):
                    c = (d, "yol", la, p, q)
                else:
                    continue
                if best is None or c[0] < best[0]:
                    if c[1] == "via":
                        if not any(copper_clear(p, MM(dd / 2), net, COPPER) for dd in (VIA_D, 0.45)):
                            continue
                    else:
                        if not all(copper_clear(_lerp(p, q, k / 20), w / 2, net, (la,)) for k in range(21)):
                            continue
                    best = c
            if best and best[0] == 0:
                break
        if best and best[0] == 0:
            break
    if best is None:
        return False
    _, kind, lay, p, q = best
    if kind == "via":
        d, dr = (VIA_D, VIA_DR) if copper_clear(p, MM(VIA_D / 2), net, COPPER) else (0.45, 0.2)
        add_via(net, p, d, dr)
    else:
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(p)
        tr.SetEnd(q)
        tr.SetWidth(w)
        tr.SetLayer(lay)
        tr.SetNet(board.FindNet(net))
        board.Add(tr)
    return True


def _item(what, x, y):
    """DRC satiri -> (net, anahtar, ped, konum) ya da None"""
    pos = pcbnew.VECTOR2I(MM(x), MM(y))
    m_pad = re.match(r"(?:PTH )?[Pp]ad (\S+) \[([^\]]*)\] of (\S+)", what)
    m_trk = re.match(r"(?:Track|Via) \[([^\]]*)\]", what)
    if m_pad:
        pads_ = find_pad(m_pad.group(3), m_pad.group(1))
        pad_ = pads_[0] if pads_ else None
        return m_pad.group(2), (m_pad.group(3), m_pad.group(1)), pad_, pad_.GetPosition() if pad_ else pos
    if m_trk:
        return m_trk.group(1), (round(x, 2), round(y, 2)), None, pos
    return None


def stitch_islands():
    """Via'siz GND yuzey adacigina adanin icinde bir via koy."""
    added = 0
    vias = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    tht = [q.GetPosition() for fp in board.GetFootprints() for q in fp.Pads()
           if q.GetNetname() == "GND" and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    r = MM(VIA_D / 2)
    for z in board.Zones():
        if z.GetZoneName() not in ("GND_F", "GND_B"):
            continue
        lay = pcbnew.F_Cu if z.GetZoneName() == "GND_F" else pcbnew.B_Cu
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            if any(ol.PointInside(v) for v in vias + tht):
                continue
            bb = ol.BBox()
            done = False
            y_ = bb.GetTop() + r
            while y_ < bb.GetBottom() - r and not done:
                x_ = bb.GetLeft() + r
                while x_ < bb.GetRight() - r and not done:
                    p = pcbnew.VECTOR2I(int(x_), int(y_))
                    ring = [pcbnew.VECTOR2I(int(p.x + r * math.cos(k * math.pi / 4)),
                                            int(p.y + r * math.sin(k * math.pi / 4))) for k in range(8)]
                    if ol.PointInside(p) and all(ol.PointInside(c) for c in ring) and \
                            point_clear(p, r, "GND"):
                        add_via("GND", p)
                        vias.append(p)
                        added += 1
                        done = True
                    x_ += MM(0.2)
                y_ += MM(0.2)
    return added


def repair_loop():
    rpt = ''
    for it in range(4):
        rpt = drc()
        n_isl = stitch_islands()
        fixed = 0
        seen = set()
        joined = 0
        for blk in rpt.split("[unconnected_items]")[1:]:
            blk = blk.split("\n[")[0]
            items = [_item(w_, float(x_), float(y_))
                     for x_, y_, w_ in re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)", blk)]
            # once iki parcayi dogrudan birlestirmeyi dene (GND disinda: GND adalari ayri)
            if len(items) == 2 and all(items) and items[0][0] == items[1][0] != "GND" and \
                    items[0][1] not in seen and items[1][1] not in seen:
                (net, ka, pa_, qa), (_, kb, pb_, qb) = items
                if join_groups(net, qa, pa_, qb, pb_):
                    seen.update((ka, kb))
                    joined += 1
                    continue
            for it_ in items:
                if not it_:
                    continue
                net, key, pad_, pos = it_
                if net not in PLANE_NETS or key in seen:
                    continue
                seen.add(key)
                if repair_group(net, pos, pad_):
                    fixed += 1
        fixed += joined
        print(f"onarim turu {it + 1}: {fixed - joined} grup duzleme baglandi, {joined} parca "
              f"birlestirildi, {n_isl} GND adaciga via")
        if not fixed and not n_isl:
            break
    return drc()


rpt = repair_loop()
n_unc = int((re.findall(r"Found (\d+) unconnected pads", rpt) or ["0"])[0])
SES2 = os.path.join(WORK, "t3-redstone-2.ses")
if n_unc and "--no-route" in sys.argv and os.path.exists(SES2):
    import_ses(SES2)                                   # onceki ikinci turun sonucu
    rpt = repair_loop()
elif n_unc and "--ikinci-tur" in sys.argv:
    # ikinci tur: mevcut yollar yerinde, Freerouting yalnizca eksikleri tamamlar
    print(f"{n_unc} bagsiz ped -> ikinci Freerouting turu", flush=True)
    MID = os.path.join(WORK, "mid-route.kicad_pcb")
    pcbnew.SaveBoard(MID, board)
    freeroute(MID, os.path.join(WORK, "t3-redstone-2.dsn"), SES2, "20", "freerouting2.log",
              optimize=False)
    if os.path.exists(SES2):
        board = pcbnew.LoadBoard(MID)
        gnd = board.FindNet("GND")
        import_ses(SES2)
        rpt = repair_loop()

unlock_prefan()
pcbnew.SaveBoard(PCB, board)

# --------------------------------------------------------------------------- DRC
rpt = open(DRC).read()
m = re.findall(r"\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors) \*\*", rpt)
print("DRC:", ", ".join(f"{n} {k}" for n, k in m) or "rapor okunamadi")
kinds = {}
for k in re.findall(r"^\[(\w+)\]", rpt, re.M):
    kinds[k] = kinds.get(k, 0) + 1
for k, n in sorted(kinds.items(), key=lambda x: -x[1]):
    print(f"   {k}: {n}")
print("rapor:", DRC)
