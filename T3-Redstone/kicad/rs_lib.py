"""T3-Redstone - ortak: kart katmanlari, stackup, projeye ozel footprint'ler.

Kutuphanede olmayan tek footprint servo header'i (3 x 8, 2.54 mm); burada
uretilir ve T3RS.pretty/ altina yazilir. Geri kalan her sey KiCad'in resmi
kutuphanesinden gelir.
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_LIB = os.path.join(HERE, "T3RS.pretty")

# KIRMIZI lehim maskesi + ENIG, 4 katman 1.6 mm (JLC 7628 benzeri)
STACKUP = '''    (stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Red") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Red") (thickness 0.01))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )'''


def _u():
    return str(uuid.uuid4())


def servo_header(cols=8, pitch=2.54):
    """3 x cols erkek header. Her sutun bir servo: satir 0 = sinyal, 1 = +5V, 2 = GND.
    Pin numarasi = 3*sutun + satir + 1. Origin = pin 1."""
    name = f"Servo_3x{cols:02d}_P2.54mm"
    w = (cols - 1) * pitch
    lines = [f'(footprint "{name}" (version 20221018) (generator "t3-redstone")',
             '  (layer "F.Cu")',
             f'  (descr "Servo header 3x{cols}, 2.54mm. Satir: sinyal / +5V / GND")',
             '  (tags "servo header PWM")',
             '  (attr through_hole)',
             f'  (fp_text reference "REF**" (at {w / 2:.2f} -2.6) (layer "F.SilkS") (tstamp "{_u()}")',
             '    (effects (font (size 1 1) (thickness 0.15))))',
             f'  (fp_text value "{name}" (at {w / 2:.2f} 7.7) (layer "F.Fab") (tstamp "{_u()}")',
             '    (effects (font (size 1 1) (thickness 0.15))))']
    x1, y1, x2, y2 = -1.27, -1.27, w + 1.27, 2 * pitch + 1.27
    for lay, e, wd in (("F.SilkS", 0.11, 0.12), ("F.Fab", 0.0, 0.1), ("F.CrtYd", 0.5, 0.05)):
        lines.append(f'  (fp_rect (start {x1 - e:.2f} {y1 - e:.2f}) (end {x2 + e:.2f} {y2 + e:.2f}) '
                     f'(stroke (width {wd}) (type solid)) (fill none) (layer "{lay}") (tstamp "{_u()}"))')
    # sinyal satiri isareti: pin 1 kosesi
    lines.append(f'  (fp_line (start -1.65 -1.65) (end -1.65 0) (stroke (width 0.12) (type solid)) '
                 f'(layer "F.SilkS") (tstamp "{_u()}"))')
    for c in range(cols):
        for r in range(3):
            n = 3 * c + r + 1
            shape = "rect" if n == 1 else "oval"
            lines.append(f'  (pad "{n}" thru_hole {shape} (at {c * pitch:.2f} {r * pitch:.2f}) '
                         f'(size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") (tstamp "{_u()}"))')
    lines.append(')')
    return name, "\n".join(lines) + "\n"


def make_local_footprints():
    os.makedirs(LOCAL_LIB, exist_ok=True)
    name, text = servo_header()
    path = os.path.join(LOCAL_LIB, name + ".kicad_mod")
    old = open(path).read() if os.path.exists(path) else None
    # tstamp'ler her seferinde degismesin: icerik ayniysa dosyaya dokunma
    if old is None or _strip_uuid(old) != _strip_uuid(text):
        open(path, "w").write(text)
    return LOCAL_LIB


def _strip_uuid(s):
    import re
    return re.sub(r'\(tstamp "[^"]*"\)', "", s)


# ----------------------------------------------------------------- semboller
LOCAL_SYM = os.path.join(HERE, "T3RS.kicad_sym")


def _pin(kind, x, y, ang, name, num, length=2.54):
    return (f'      (pin {kind} line (at {x:.2f} {y:.2f} {ang}) (length {length})\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27)))))')


def _symbol(name, ref, value, fp, ds, w, h, pins, desc):
    hw, hh = w / 2, h / 2
    out = [f'  (symbol "{name}" (in_bom yes) (on_board yes)',
           f'    (property "Reference" "{ref}" (at {-hw:.2f} {hh + 1.27:.2f} 0) '
           '(effects (font (size 1.27 1.27)) (justify left)))',
           f'    (property "Value" "{value}" (at {-hw:.2f} {-hh - 1.27:.2f} 0) '
           '(effects (font (size 1.27 1.27)) (justify left)))',
           f'    (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "Datasheet" "{ds}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "ki_description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (symbol "{name}_0_1"',
           f'      (rectangle (start {-hw:.2f} {hh:.2f}) (end {hw:.2f} {-hh:.2f}) '
           '(stroke (width 0.254) (type default)) (fill (type background))))',
           f'    (symbol "{name}_1_1"']
    out += pins
    out += ['    )', '  )']
    return out


def drv8874_symbol():
    # TI SLVSF66: PWP 16 pin + PowerPAD
    L = [("1", "EN/IN1", "input"), ("2", "PH/IN2", "input"), ("3", "~{nSLEEP}", "input"),
         ("4", "~{nFAULT}", "open_collector"), ("5", "VREF", "input"), ("6", "IPROPI", "output"),
         ("7", "IMODE", "input"), ("16", "PMODE", "input")]
    Rr = [("11", "VM", "power_in"), ("12", "VCP", "passive"), ("13", "CPH", "passive"),
          ("14", "CPL", "passive"), ("8", "OUT1", "output"), ("10", "OUT2", "output")]
    pins = []
    for i, (n, nm, k) in enumerate(L):
        pins.append(_pin(k, -12.7, 8.89 - 2.54 * i, 0, nm, n))
    for i, (n, nm, k) in enumerate(Rr):
        pins.append(_pin(k, 12.7, 8.89 - 2.54 * i - (2.54 if i >= 4 else 0), 180, nm, n))
    for i, (n, nm) in enumerate((("9", "PGND"), ("15", "GND"), ("17", "PAD"))):
        pins.append(_pin("power_in", -2.54 + 2.54 * i, -15.24, 90, nm, n))
    return _symbol("DRV8874PWP", "U", "DRV8874PWP",
                   "Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm_ThermalVias",
                   "https://www.ti.com/lit/ds/symlink/drv8874.pdf", 20.32, 25.4, pins,
                   "37V 6A H-kopru surucu, IPROPI akim cikisli")


def servo_symbol(cols=8):
    pins = []
    for i in range(cols):
        y = 8.89 - 2.54 * i
        pins.append(_pin("passive", -13.97, y, 0, f"S{i + 1}", str(3 * i + 1)))
        pins.append(_pin("passive", 13.97, y, 180, f"+{i + 1}", str(3 * i + 2)))
        pins.append(_pin("passive", -8.89 + 2.54 * i, -13.97, 90, f"-{i + 1}", str(3 * i + 3)))
    return _symbol(f"Servo_3x{cols:02d}", "J", f"Servo_3x{cols:02d}",
                   f"T3RS:Servo_3x{cols:02d}_P2.54mm", "", 22.86, 22.86, pins,
                   "Servo header: sinyal / +V / GND")


def make_local_symbols():
    lines = ['(kicad_symbol_lib (version 20220914) (generator t3-redstone)']
    lines += drv8874_symbol() + servo_symbol()
    lines.append(')')
    text = "\n".join(lines) + "\n"
    old = open(LOCAL_SYM).read() if os.path.exists(LOCAL_SYM) else None
    if old != text:
        open(LOCAL_SYM, "w").write(text)
    return LOCAL_SYM
