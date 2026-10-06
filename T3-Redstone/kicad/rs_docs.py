#!/usr/bin/env python3
"""rs_design.py -> ../docs/04-netlist.md  (net -> pin listesi, otomatik)"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_design as D          # noqa: E402

OUT = os.path.join(HERE, "..", "docs", "04-netlist.md")


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


nets = {}
for p in D.PARTS:
    for pin, n in p["nets"].items():
        if n:
            nets.setdefault(n, []).append(f"{p['ref']}.{pin}")
parts = [p for p in D.PARTS if not p["ref"].startswith("MH")]
L = ["# T3-Redstone — Bağlantı Listesi (netlist)", "",
     "> Bu dosya `kicad/rs_docs.py` ile `kicad/rs_design.py`'den **üretilir** — elle düzenleme.",
     "> Şema (`kicad/t3-redstone.kicad_sch`) ve kart aynı kaynaktan gelir; `rs_sch.py --check`",
     "> şemadan çıkan netlisti bu tabloyla pin pin karşılaştırır.", "",
     f"Toplam **{len(nets)} net**, **{len(parts)} komponent** (+{len(D.PARTS) - len(parts)} montaj deliği).", "",
     "| Net | Bağlı uçlar |", "|---|---|"]
for n in sorted(nets, key=lambda k: (k not in ("GND", "VBAT_RAW", "VBAT_F", "VBAT", "VSYS", "VBAT_SW",
                                                "+5V", "+3V3"), natural(k))):
    L.append(f"| `{n}` | {', '.join(sorted(nets[n], key=natural))} |")
L += ["", "## Pinout doğrulaması", "",
      "| Parça | Kaynak | Durum |", "|---|---|---|",
      "| ESP32-S3-WROOM-1U | KiCad `RF_Module:ESP32-S3-WROOM-1` sembolü + resmi `ESP32-S3-WROOM-1U` footprint'i | ✔ |",
      "| INA226 (VSSOP-10) | KiCad `Sensor_Energy:INA226` | ✔ |",
      "| PCA9685PW (TSSOP-28) | KiCad `Driver_LED:PCA9685PW` | ✔ |",
      "| TPS563201 (SOT-23-6) | KiCad `Regulator_Switching:TPS563200` (aynı pinout) | ✔ |",
      "| AP2112K-3.3 (SOT-23-5) | KiCad `Regulator_Linear:AP2112K-3.3` | ✔ |",
      "| SK6812MINI | KiCad `LED:SK6812MINI` — 1=DOUT 2=VSS 3=DIN 4=VDD | ✔ |",
      "| 74LVC245 (TSSOP-20) | KiCad `74xx:74HC245` (aynı pinout) | ✔ |",
      "| 74AHCT1G125 (SOT-23-5) | KiCad `74xGxx:74AHCT1G125` | ✔ |",
      "| USBLC6-2SC6 | KiCad `Power_Protection:USBLC6-2SC6` | ✔ |",
      "| AO4407A (SO-8) | KiCad `Transistor_FET:FDS9435A` ile aynı: 1-3 S, 4 G, 5-8 D | ✔ |",
      "| AO3400A (SOT-23) | KiCad `Transistor_FET:AO3400A`: 1 G, 2 S, 3 D | ✔ |",
      "| B5819W (SOD-123) | KiCad `Diode_SMD:D_SOD-123`: **pad 1 = katot** | ✔ |",
      "| DRV8874 (HTSSOP-16) | KiCad'de yok. TI SLVSF66: 1 EN/IN1, 2 PH/IN2, 3 nSLEEP, 4 nFAULT, 5 VREF, "
      "6 IPROPI, 7 IMODE, 8 OUT1, 9 PGND, 10 OUT2, 11 VM, 12 VCP, 13 CPH, 14 CPL, 15 GND, 16 PMODE | "
      "⚠ siparişten önce veri sayfasıyla bir kez daha bak |",
      ""]
open(OUT, "w").write("\n".join(L))
print(f"netlist: {OUT}  ({len(nets)} net)")
