#!/usr/bin/env python3
"""T3-Redstone -> t3-redstone.kicad_sch  (rs_design.py'den sema uretir)

KiCad'in resmi sembolleri kullanilir (DRV8874 ve servo header projeye ozel:
T3RS.kicad_sym). Her pine kisa bir tel + net etiketi baglanir; GND / +3V3 / +5V
icin guc sembolu kullanilir. Bos pinlere "no connect" konur.

Dogrulama: kicad-cli ile semadan netlist cikarilir ve rs_design.py ile pin pin
karsilastirilir (python3 rs_sch.py --check).
"""
import math
import os
import re
import subprocess
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_design as D                    # noqa: E402
from rs_lib import make_local_symbols    # noqa: E402

SYMROOT = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
SCH = os.path.join(HERE, "t3-redstone.kicad_sch")
PROJECT = "t3-redstone"
G = 1.27


def U():
    return str(uuid.uuid4())


ROOT = "8e1f3c2a-7d5b-4b1e-9a3f-2c6d5e4f3a21"     # sabit: tekrar uretimde fark cikmasin

# ------------------------------------------------------------ parca -> sembol
LIB = {
    "J1": "Connector_Generic:Conn_02x20_Odd_Even", "U1": "RF_Module:ESP32-S3-WROOM-1",
    "SW1": "Switch:SW_Push", "SW2": "Switch:SW_Push",
    "J11": "Connector:USB_C_Receptacle_USB2.0_16P", "U10": "Power_Protection:USBLC6-2SC6",
    "D1": "Device:D_Schottky", "D2": "Device:D_Schottky",
    "J2": "Connector_Generic:Conn_01x02", "F1": "Device:Fuse",
    "Q1": "Transistor_FET:FDS9435A", "Q2": "Transistor_FET:FDS9435A",
    "Q3": "Transistor_FET:AO3400A", "Q4": "Transistor_FET:AO3400A",
    "U5": "Sensor_Energy:INA226", "U7": "Regulator_Switching:TPS563200",
    "U6": "Regulator_Linear:AP2112K-3.3", "L1": "Device:L",
    "J3": "Connector:Screw_Terminal_01x02", "J4": "Connector:Screw_Terminal_01x02",
    "J5": "Connector:Screw_Terminal_01x02",
    "J12": "Connector_Generic:Conn_01x02", "LS1": "Connector_Generic:Conn_01x02",
    "J13": "Connector_Generic:Conn_01x03", "J6": "Connector_Generic:Conn_01x04",
    "J7": "Connector_Generic:Conn_01x04", "J14": "Connector_Generic:Conn_01x04",
    "J10": "Connector_Generic_MountingPin:Conn_01x04_MountingPin",
    "U2": "T3RS:DRV8874PWP", "U3": "T3RS:DRV8874PWP",
    "J8A": "T3RS:Servo_3x08", "J8B": "T3RS:Servo_3x08",
    "U8": "74xx:74HC245", "RN1": "Device:R_Pack04", "U4": "Driver_LED:PCA9685PW",
    "U9": "74xGxx:74AHCT1G125", "C8": "Device:C_Polarized",
}


def lib_for(p):
    r = p["ref"]
    if r in LIB:
        return LIB[r]
    if r.startswith("DS"):
        return "LED:SK6812MINI"
    if r.startswith("MH"):
        return "Mechanical:MountingHole"
    if r.startswith("RS") or p["fp"].startswith("Resistor_SMD:R_0"):
        return "Device:R"
    if p["fp"].startswith("Capacitor_SMD:C_"):
        return "Device:C"
    raise KeyError(r)


# ------------------------------------------------------- s-ifade okuma / yazma
class Q(str):
    """tirnakli dizgi"""


def parse(text):
    st = [[]]
    for t in re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text):
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(Q(t[1:-1].replace('\\"', '"')) if t.startswith('"') else t)
    return st[0][0]


def dump(n, ind=0):
    """S-ifadeyi yaz; atom/liste sirasi korunur (KiCad sira duyarli: 'hide' vb.)."""
    if not isinstance(n, list):
        return '"' + n.replace('"', '\\"') + '"' if isinstance(n, Q) else str(n)
    if all(not isinstance(c, list) for c in n) or ind > 6:
        return "(" + " ".join(dump(c, ind + 1) for c in n) + ")"
    pad = "\n" + "  " * (ind + 1)
    out = "(" + dump(n[0])
    for c in n[1:]:
        out += (pad + dump(c, ind + 1)) if isinstance(c, list) else (" " + dump(c, ind + 1))
    return out + ")"


def kids(n, key):
    return [c for c in n if isinstance(c, list) and c and c[0] == key]


_LIBS = {}


def lib_symbol(lib_id):
    """Kutuphaneden sembolu al, 'extends' varsa duzlestir, adini Lib:Ad yap."""
    lib, name = lib_id.split(":")
    if lib not in _LIBS:
        path = make_local_symbols() if lib == "T3RS" else os.path.join(SYMROOT, lib + ".kicad_sym")
        _LIBS[lib] = {s[1]: s for s in kids(parse(open(path).read()), "symbol")}
    syms = _LIBS[lib]
    s = syms[name]
    ext = kids(s, "extends")
    if ext:
        base = syms[ext[0][1]]
        props = kids(s, "property")
        body = [c for c in base if isinstance(c, list) and c[0] not in ("property", "symbol")]
        subs = []
        for sub in kids(base, "symbol"):
            sub = list(sub)
            sub[1] = Q(sub[1].replace(ext[0][1], name, 1))
            subs.append(sub)
        s = ["symbol", Q(name)] + body + props + subs
    s = list(s)
    s[1] = Q(lib_id)
    return s


def pins_of(sym):
    """[(numara, x, y, aci, tip)]  (sembol koordinati, Y yukari)"""
    out = []
    for sub in kids(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", sub[1])
        if m and m.group(1) not in ("0", "1"):
            continue                                    # tek birimli parcalar
        for p in kids(sub, "pin"):
            at = kids(p, "at")[0]
            num = kids(p, "number")[0][1]
            out.append((str(num), float(at[1]), float(at[2]), int(float(at[3]) if len(at) > 3 else 0), p[1]))
    return out


def bbox(sym):
    xs, ys = [0.0], [0.0]
    for n, x, y, a, k in pins_of(sym):
        xs.append(x)
        ys.append(y)
    for sub in kids(sym, "symbol"):
        for r in kids(sub, "rectangle"):
            for key in ("start", "end"):
                v = kids(r, key)[0]
                xs.append(float(v[1]))
                ys.append(float(v[2]))
    return min(xs), min(ys), max(xs), max(ys)


# ------------------------------------------------------------------ yerlesim
POWER = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V"}
PAPER_W, PAPER_H = 841.0, 594.0                    # A1
LBL = 17.78                                         # etiket payi


def snap(v):
    return round(v / 2.54) * 2.54


items = []                                          # cikti s-ifadeleri (metin)
used_libs = {}
pwr_n = [0]


def eff(size=1.27, justify=None, hide=False):
    j = f" (justify {justify})" if justify else ""
    return f"(effects (font (size {size} {size})){j}{' hide' if hide else ''})"


def place_symbol(lib_id, ref, value, x, y, rot=0, fp="", extra=None, unit=1):
    sym = used_libs.setdefault(lib_id, lib_symbol(lib_id))
    x0, y0, x1, y1 = bbox(sym)
    props = [f'(property "Reference" "{ref}" (at {x:.2f} {y - y1 - 2.54:.2f} 0) {eff(justify="left") if not ref.startswith("#") else eff(hide=True)})',
             f'(property "Value" "{value}" (at {x:.2f} {y - y0 + 2.54:.2f} 0) {eff(justify="left")})',
             f'(property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})',
             f'(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})']
    for k, v in (extra or {}).items():
        props.append(f'(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
    pins = "".join(f'\n    (pin "{n}" (uuid {U()}))' for n in sorted({p[0] for p in pins_of(sym)}))
    items.append(f'  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit {unit})\n'
                 f'    (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no)\n'
                 f'    (uuid {U()})\n    ' + "\n    ".join(props) + pins +
                 f'\n    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit {unit}))))\n  )')
    return sym


def wire(a, b):
    items.append(f'  (wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) '
                 f'(stroke (width 0) (type default)) (uuid {U()}))')


def label(net, p, d):
    ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
    just = "left" if ang in (0, 90) else "right"
    items.append(f'  (label "{net}" (at {p[0]:.2f} {p[1]:.2f} {ang}) (fields_autoplaced) '
                 f'{eff(justify=just + " bottom")} (uuid {U()}))')


def power(net, p, d):
    lib_id = POWER[net]
    # GND govdesi asagi, +V govdesi yukari bakar; disari yonune dondur
    if net == "GND":
        rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
    else:
        rot = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[d]
    pwr_n[0] += 1
    place_symbol(lib_id, f"#PWR{pwr_n[0]:03d}", net, p[0], p[1], rot)


def noconnect(p):
    items.append(f'  (no_connect (at {p[0]:.2f} {p[1]:.2f}) (uuid {U()}))')


def build():
    x, y, row_h = 25.4, 25.4, 0.0
    for part in D.PARTS:
        lib_id = lib_for(part)
        sym = used_libs.setdefault(lib_id, lib_symbol(lib_id))
        x0, y0, x1, y1 = bbox(sym)
        w = (x1 - x0) + 2 * LBL + 5.08
        h = (y1 - y0) + 2 * LBL
        if x + w > PAPER_W - 25.4:
            x, y, row_h = 25.4, y + row_h, 0.0
        sx, sy = snap(x + LBL - x0 + 2.54), snap(y + LBL + y1)
        extra = {"MPN": part["mpn"]} if part["mpn"] else {}
        if part["desc"]:
            extra["Not"] = part["desc"]
        place_symbol(lib_id, part["ref"], part["value"], sx, sy, 0, part["fp"], extra)
        done = {}
        for num, px, py, ang, kind in pins_of(sym):
            p = (round(sx + px, 2), round(sy - py, 2))
            net = part["nets"].get(num, "")
            if p in done:
                if done[p] != net:
                    sys.exit(f"{part['ref']}: ust uste pinler farkli netlerde ({num}: {net} / {done[p]})")
                continue
            done[p] = net
            if not net:
                if not part["ref"].startswith("MH"):
                    noconnect(p)
                continue
            a = math.radians(ang)
            d = (-round(math.cos(a)), round(math.sin(a)))      # disari yon (sema, Y asagi)
            q = (round(p[0] + d[0] * 2.54, 2), round(p[1] + d[1] * 2.54, 2))
            wire(p, q)
            if net in POWER:
                power(net, q, d)
            else:
                label(net, q, d)
        x += w
        row_h = max(row_h, h)
    return y + row_h


def write():
    used_libs.clear()
    items.clear()
    bottom = build()
    if bottom > PAPER_H:
        print(f"UYARI: sema kagidi tasti ({bottom:.0f} mm)")
    libsyms = "\n".join("    " + dump(s, 2).replace("\n", "\n  ") for s in used_libs.values())
    out = [f'(kicad_sch (version 20230121) (generator eeschema)',
           f'  (uuid {ROOT})',
           '  (paper "A1")',
           '  (title_block (title "T3-Redstone") (rev "B") (company "ROS 2 robot kontrol karti - T3 Gemstone O1")',
           '    (comment 1 "kicad/rs_sch.py ile rs_design.py\'den uretildi - elle degistirme, kaynagi duzenle"))',
           '  (lib_symbols', libsyms, '  )']
    out += items
    out += ['  (sheet_instances (path "/" (page "1")))', ')']
    open(SCH, "w").write("\n".join(out) + "\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n'
        '  (lib (name "T3RS")(type "KiCad")(uri "${KIPRJMOD}/T3RS.kicad_sym")(options "")'
        '(descr "T3-Redstone projeye ozel semboller"))\n)\n')
    print(f"sema: {SCH}  ({len([i for i in items if i.startswith('  (symbol')])} sembol)")


# ------------------------------------------------------------------- denetim
def check():
    net_file = os.path.join(HERE, "build", "sch.net")
    os.makedirs(os.path.dirname(net_file), exist_ok=True)
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", net_file, SCH], check=True, stdout=subprocess.DEVNULL)
    nl = parse(open(net_file).read())
    sch = {}
    for n in kids(kids(nl, "nets")[0], "net"):
        name = kids(n, "name")[0][1].lstrip("/")
        for node in kids(n, "node"):
            ref, pin = kids(node, "ref")[0][1], kids(node, "pin")[0][1]
            if ref.startswith("#"):
                continue
            sch[(ref, pin)] = name
    errs = 0
    for part in D.PARTS:
        for pin, net in part["nets"].items():
            if not net:
                continue
            got = sch.get((part["ref"], pin))
            if got != net:
                errs += 1
                print(f"  FARK {part['ref']}.{pin}: tasarim={net} sema={got}")
    # semada tasarimda olmayan baglanti
    for (ref, pin), net in sch.items():
        part = next((p for p in D.PARTS if p["ref"] == ref), None)
        if part and not part["nets"].get(pin) and not net.startswith("unconnected"):
            errs += 1
            print(f"  FAZLA {ref}.{pin}: sema={net}")
    print("SEMA <-> TASARIM:", "birebir ayni" if not errs else f"{errs} fark")
    return errs


if __name__ == "__main__":
    write()
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
