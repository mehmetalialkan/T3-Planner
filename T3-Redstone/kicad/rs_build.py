#!/usr/bin/env python3
"""T3-Redstone -> t3-redstone.kicad_pcb  (KiCad 7 pcbnew Python API ile)

Yaptigi: kontur + kesit, resmi kutuphane footprint'leri, netler, yerlesim,
4 katman (In1 = GND duzlemi, In2 = bolunmus guc duzlemi), stackup (kirmizi maske,
ENIG), guc yollari, ipek baski. Sinyal yollari rs_route.py ile cizilir.

    python3 rs_build.py          # yerlesim + guc
    python3 rs_route.py          # Freerouting + bakir dolgu + DRC
"""
import json
import math
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_design as D                       # noqa: E402
from rs_lib import STACKUP, make_local_footprints   # noqa: E402

FPROOT = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
PCB = os.path.join(HERE, "t3-redstone.kicad_pcb")
PRO = os.path.join(HERE, "t3-redstone.kicad_pro")
ORGX, ORGY = 30.0, 30.0                     # kart sol-alt kosesinin sayfadaki yeri (ust kenar)
MM = pcbnew.FromMM


def V(x, y):
    """kart koordinati (mm, Y yukari) -> KiCad (nm, Y asagi)"""
    return pcbnew.VECTOR2I(MM(ORGX + x), MM(ORGY + D.BH - y))


def BXY(v):
    """KiCad -> kart koordinati"""
    return (pcbnew.ToMM(v.x) - ORGX, D.BH - (pcbnew.ToMM(v.y) - ORGY))


# ----------------------------------------------------------------------------- kart
board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
tb = board.GetTitleBlock()
tb.SetTitle("T3-Redstone")
tb.SetRevision("B")
tb.SetCompany("ROS 2 robot kontrol karti - T3 Gemstone O1")
tb.SetComment(0, "4 katman / KIRMIZI maske / ENIG / 1.6 mm")
tb.SetComment(1, "F.Cu sinyal - In1.Cu GND - In2.Cu guc - B.Cu sinyal")
tb.SetComment(2, "Uretici: kicad/rs_build.py + rs_route.py")

NETS = {}


def net(name):
    if not name:
        return None
    if name not in NETS:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        NETS[name] = ni
    return NETS[name]


net("GND")

# -------------------------------------------------------------------------- kontur
EDGE = pcbnew.Edge_Cuts


def seg(a, b, layer=EDGE, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a))
    s.SetEnd(V(*b))
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    board.Add(s)


def arc(cx, cy, r, a1, a2, layer=EDGE, w=0.1):
    p = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
         for a in (a1, (a1 + a2) / 2, a2)]
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(V(*p[0]), V(*p[1]), V(*p[2]))
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    board.Add(s)


W, H, Rr, cu = D.BW, D.BH, D.BR, D.CUT
seg((Rr, 0), (cu["x1"], 0))
seg((cu["x2"], 0), (W - Rr, 0))
seg((cu["x1"], 0), (cu["x1"], cu["depth"] - cu["r"]))
seg((cu["x2"], cu["depth"] - cu["r"]), (cu["x2"], 0))
seg((cu["x1"] + cu["r"], cu["depth"]), (cu["x2"] - cu["r"], cu["depth"]))
arc(cu["x1"] + cu["r"], cu["depth"] - cu["r"], cu["r"], 180, 90)
arc(cu["x2"] - cu["r"], cu["depth"] - cu["r"], cu["r"], 90, 0)
seg((W, Rr), (W, H - Rr))
seg((W - Rr, H), (Rr, H))
seg((0, H - Rr), (0, Rr))
arc(W - Rr, Rr, Rr, 270, 360)
arc(W - Rr, H - Rr, Rr, 0, 90)
arc(Rr, H - Rr, Rr, 90, 180)
arc(Rr, Rr, Rr, 180, 270)

OUTLINE = [(0, 0), (cu["x1"], 0), (cu["x1"], cu["depth"]), (cu["x2"], cu["depth"]),
           (cu["x2"], 0), (W, 0), (W, H), (0, H)]

# --------------------------------------------------------------------- footprintler
LOCAL = make_local_footprints()
FP = {}
FP_REF_AT = {}


def libpath(lib):
    return LOCAL if lib == "T3RS" else os.path.join(FPROOT, lib + ".pretty")


def courtyard(fp):
    lay = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == lay:
            bb = g.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:                                   # courtyard yoksa padler
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
    x1, y1 = BXY(pcbnew.VECTOR2I(min(xs), max(ys)))
    x2, y2 = BXY(pcbnew.VECTOR2I(max(xs), min(ys)))
    return (x1, y1, x2, y2)


problems = []
for p in D.PARTS:
    lib, name = p["fp"].split(":")
    fp = pcbnew.FootprintLoad(libpath(lib), name)
    if fp is None:
        sys.exit(f"footprint bulunamadi: {p['fp']}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(p["ref"])
    fp.SetValue(p["value"])
    if p["mpn"]:
        fp.SetProperty("MPN", p["mpn"])
    if p["desc"]:
        fp.SetProperty("Not", p["desc"])
    board.Add(fp)
    fp.SetPosition(V(0, 0))
    if p["side"] == "B":
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(p["rot"])
    if p["anchor"] == "pin1":
        pad1 = [q for q in fp.Pads() if q.GetNumber() == "1"][0]
        px, py = BXY(pad1.GetPosition())
        dx, dy = p["x"] - px, p["y"] - py
    else:
        x1, y1, x2, y2 = courtyard(fp)
        dx, dy = p["x"] - (x1 + x2) / 2, p["y"] - (y1 + y2) / 2
    fp.Move(pcbnew.VECTOR2I(MM(dx), MM(-dy)))
    # pad -> net
    numbers = {q.GetNumber() for q in fp.Pads()}
    for k in p["nets"]:
        if k not in numbers:
            problems.append(f"{p['ref']}: footprint'te '{k}' pad'i yok")
    for q in fp.Pads():
        n = p["nets"].get(q.GetNumber())
        if n:
            q.SetNet(net(n))
        elif q.GetNumber() and q.GetNumber() not in p["nets"] and p["nets"]:
            problems.append(f"{p['ref']}.{q.GetNumber()} tanimsiz (bos birakildi)")
    # termal: via dizili pedler dogrudan, sik header pinleri 45 derece spoke
    for q in fp.Pads():
        if q.GetNumber() in D.PAD_FULL.get(p["ref"], ()):
            q.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        if p["ref"] in D.SPOKE45 and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            q.SetThermalSpokeAngleDegrees(45)
    # referans yazisi: kucuk, ipek baskida
    ref = fp.Reference()
    ref.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
    ref.SetTextThickness(MM(0.12))
    # kucuk pasiflerin ve kenara sigmayanlarin referansi fabrikasyon katmanina
    if re.match(r"(R|C|L|D)\d|RN|RS|MH|DS|J8A$|J11$|J12$|LS1$|J2$|Q\d|U([2-35-7]|9|10)$", p["ref"]):
        ref.SetLayer(pcbnew.B_Fab if p["side"] == "B" else pcbnew.F_Fab)
    FP_REF_AT[p["ref"]] = None
    # footprint'in kendi "1" gibi ek ipek yazilari (LED pin-1) pedlerin ustune dusuyor
    for g in list(fp.GraphicalItems()):
        if g.GetClass() in ("FP_TEXT", "PCB_TEXT") and g.GetLayer() == pcbnew.F_SilkS \
                and g.GetText() not in ("${REFERENCE}",):
            g.SetVisible(False)
    FP[p["ref"]] = fp
    # IC / transistor / XT60 referansi govdenin ortasina (pedsiz bolge)
    if re.match(r"U([2-9]|10)$|Q\d|J2$|F1$", p["ref"]):
        ref.SetPosition(fp.GetPosition() if p["ref"] != "J2" else V(p["x"], p["y"]))
        ref.SetTextAngleDegrees(0)
    if p["ref"] == "U1":                                   # modul ust kismi pedsiz
        ref.SetPosition(V(p["x"], p["y"] + 8.6))
        ref.SetTextAngleDegrees(0)

# J1 yon kontrolu: pin 2 kenara (yukari), pin 3 saga
_j1 = {q.GetNumber(): BXY(q.GetPosition()) for q in FP["J1"].Pads()}
assert abs(_j1["2"][1] - _j1["1"][1] - 2.54) < 0.01 and abs(_j1["3"][0] - _j1["1"][0] - 2.54) < 0.01, \
    f"J1 pin duzeni yanlis: {_j1['1']} {_j1['2']} {_j1['3']}"


# ------------------------------------------------------------- yerlesim denetimi
def placement_check():
    out = []
    boxes = {r: (courtyard(f), f.IsFlipped()) for r, f in FP.items()}
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        (ax1, ay1, ax2, ay2), af = boxes[a]
        for b in refs[i + 1:]:
            (bx1, by1, bx2, by2), bf = boxes[b]
            if af != bf:
                continue
            ox = min(ax2, bx2) - max(ax1, bx1)
            oy = min(ay2, by2) - max(ay1, by1)
            if ox > 0.01 and oy > 0.01:
                out.append(f"CAKISMA {a} <-> {b}  ({ox:.2f} x {oy:.2f} mm)")
        if a.startswith("MH"):
            continue
        x1, y1, x2, y2 = boxes[a][0]
        if (x1 < -0.01 or y1 < -0.01 or x2 > D.BW + 0.01 or y2 > D.BH + 0.01) \
                and a not in ("J11",):           # USB-C agzi kenardan bilerek tasar
            out.append(f"KART DISI {a} ({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f})")
        if x2 > cu["x1"] and x1 < cu["x2"] and y1 < cu["depth"]:
            out.append(f"KESIT {a} ({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f})")
    return out


# -------------------------------------------------------------------- bakir alanlar
def zone(netname, layers, poly, prio=0, name="", clearance=0.2, thermal=True, minw=0.2,
         gap=0.25, spoke=0.3):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for lay in layers:
        ls.AddLayer(lay)
    z.SetLayerSet(ls)
    z.SetNet(net(netname))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        v = V(x, y)
        ol.Append(v.x, v.y)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(MM(gap))
    z.SetThermalReliefSpokeWidth(MM(spoke))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)   # bagsiz adacik birakma
    z.SetZoneName(name)
    board.Add(z)
    return z


# ic duzlemler THT pedlere DOGRUDAN baglanir: sik header'larda (2.54 mm) aradaki
# vialar termal kollari keser, pin bagsiz kalir
zone("GND", [pcbnew.In1_Cu], OUTLINE, 0, "GND_DUZLEMI", thermal=False)
for nm, poly in D.IN2_SPLIT:
    zone(nm, [pcbnew.In2_Cu], poly, 1, f"IN2_{nm}", thermal=False)

# ------------------------------------------------------------------------ guc yollari
TRACKS = []


def pad(ref, num):
    for q in FP[ref].Pads():
        if q.GetNumber() == str(num):
            return BXY(q.GetPosition())
    raise KeyError(f"{ref}.{num}")


def track(netname, pts, width, layer=pcbnew.F_Cu):
    pts = [pad(*p) if isinstance(p[0], str) else p for p in pts]
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(MM(width))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        t.SetLocked(True)
        board.Add(t)
        TRACKS.append(t)


def via(netname, xy, size=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(*xy))
    v.SetWidth(MM(size))
    v.SetDrill(MM(drill))
    v.SetNet(net(netname))
    v.SetLocked(True)
    board.Add(v)


for t in D.POWER_TRACKS:
    track(t["net"], t["pts"], t["w"], pcbnew.B_Cu if t.get("layer") == "B" else pcbnew.F_Cu)
for v in D.POWER_VIAS:
    for xy in v["at"]:
        via(v["net"], xy, v.get("size", 0.8), v.get("drill", 0.4))
for nm, poly in D.F_POURS:
    zone(nm, [pcbnew.F_Cu], poly, 5, f"F_{nm}", clearance=0.2, thermal=False)

# --------------------------------------------------------------------------- ipek baski
def text(t, x, y, size=1.0, thick=0.15, layer=pcbnew.F_SilkS, left=True):
    tx = pcbnew.PCB_TEXT(board)
    tx.SetText(t)
    tx.SetPosition(V(x, y))
    tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    tx.SetTextThickness(MM(thick))
    if layer in (pcbnew.B_SilkS, pcbnew.B_Cu):
        tx.SetMirrored(True)
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if left else pcbnew.GR_TEXT_H_ALIGN_CENTER)
    elif left:
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(tx)


for args in D.SILK:
    text(*args)
# alt yuz: kart kimligi ve uyarilar (ust yuz kalabalik)
# ESP32 modulunun alti: alt yuzde THT ped yok
for t, y, sz in (("T3-REDSTONE rev B", 47.0, 1.6), ("ROS 2 kontrol karti", 45.0, 0.8),
                 ("T3 Gemstone O1 / 2S LiPo 6-8.4V", 43.6, 0.7),
                 ("J12 ACIL STOP (NC) - kopru yoksa motor yok", 41.6, 0.6),
                 ("LS1 BUZZER 5V   J13 BUMPER", 40.4, 0.6),
                 ("SW1 BOOT   SW2 RESET   J10 QWIIC", 39.2, 0.6),
                 ("J14: 3V3 IO16 IO17 GND", 38.0, 0.6),
                 ("40P soket >=16mm, bu yuze parca konmaz", 36.2, 0.6)):
    text(t, 18.8, y, sz, max(0.1, sz * 0.15), pcbnew.B_SilkS, left=False)
for nm, x1, y1, x2, y2 in D.TALL:                 # Gemstone'un yuksek bloklari (bilgi)
    for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        seg(a, b, pcbnew.Dwgs_User, 0.15)
    text(f"{nm} h~13.5mm (Gemstone)", x1 + 0.5, y2 - 1.2, 0.8, 0.12, pcbnew.Dwgs_User)

# ------------------------------------------------------------------------- kaydet
pcbnew.SaveBoard(PCB, board)

# stackup (kirmizi maske / ENIG) setup bolumune
s = open(PCB).read()
s = re.sub(r"\(setup\n", "(setup\n" + STACKUP + "\n", s, count=1)
open(PCB, "w").write(s)

# proje dosyasi: kurallar + net siniflari
def nc(name, d):
    return {"name": name, "clearance": d["clearance"], "track_width": d["track"],
            "via_diameter": d["via"], "via_drill": d["drill"],
            "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
            "line_style": 0, "wire_width": 6, "bus_width": 12,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}


pro = {
    "board": {
        "design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                         "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                         "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                         "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                         "silk_text_thickness": 0.15, "pads": {"drill": 1.0, "height": 1.7, "width": 1.7}},
            "rules": {"min_clearance": 0.1, "min_track_width": 0.1,
                      "min_via_diameter": 0.45, "min_via_annular_width": 0.1,
                      "min_through_hole_diameter": 0.2, "min_hole_clearance": 0.15,
                      "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3,
                      "min_silk_clearance": 0.0, "min_text_height": 0.6,
                      "min_text_thickness": 0.1, "min_microvia_diameter": 0.2,
                      "min_microvia_drill": 0.1, "solder_mask_clearance": 0.05,
                      "solder_mask_min_width": 0.0, "use_height_for_length_calcs": True,
                      "allow_blind_buried_vias": False, "allow_microvias": False,
                      # header GND pinleri ic GND duzlemine dogrudan bagli; dis dokumde
                      # tek termal kol yeterli
                      "min_resolved_spokes": 1},
            "track_widths": [0.0, 0.2, 0.3, 0.5, 1.0, 1.5, 2.0],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.5, "drill": 0.25},
                               {"diameter": 0.6, "drill": 0.3}, {"diameter": 0.8, "drill": 0.4}],
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                                "silk_overlap": "ignore", "silk_over_copper": "warning",
                                "silk_edge_clearance": "warning"},
        },
        "layer_presets": [], "viewports": [], "3dviewports": [],
    },
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": "t3-redstone.kicad_pro", "version": 1},
    "net_settings": {
        "classes": [nc("Default", D.DEFAULT)] + [nc(k, v) for k, v in D.NETCLASS.items()],
        "meta": {"version": 3},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [{"netclass": k, "pattern": n}
                              for k, v in D.NETCLASS.items() for n in v["nets"]],
    },
    "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
    "sheets": [], "text_variables": {},
}
json.dump(pro, open(PRO, "w"), indent=2)

# yerel footprint kutuphanesi tablosu
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n'
    '  (lib (name "T3RS")(type "KiCad")(uri "${KIPRJMOD}/T3RS.pretty")(options "")'
    '(descr "T3-Redstone projeye ozel footprintler"))\n)\n')

probs = placement_check() + problems
print(f"komponent {len(FP)}  net {len(NETS)}  guc yolu {len(TRACKS)}")
print("YERLESIM:", "temiz" if not probs else f"{len(probs)} sorun")
for x in probs:
    print("  -", x)
