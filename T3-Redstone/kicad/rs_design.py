"""T3-Redstone - devre tanimi (tek kaynak): parcalar, footprint'ler, netler, yerlesim.

Iki bolum:
  1) PARCALAR  - her parcanin footprint'i ve pad -> net tablosu
  2) POS       - yerlesim: ref -> (x, y, rot)

Koordinatlar KART koordinatidir: mm, sol-alt kose (0,0), Y YUKARI.
(x, y) = courtyard kutusunun MERKEZI (J1 haric: J1 pin 1'e gore konur).
rot = derece, saat yonunun tersine.

Pin numaralari KiCad'in resmi sembol kutuphanesiyle karsilastirildi:
  ESP32-S3-WROOM-1(U) RF_Module        INA226       Sensor_Energy
  PCA9685PW           Driver_LED       TPS563200    Regulator_Switching
  AP2112K-3.3         Regulator_Linear SK6812MINI   LED
  74AHCT1G125         74xGxx           USBLC6-2SC6  Power_Protection
  AO3400A / AO4407A   Transistor_FET   74HC245      74xx (LVC245 ile ayni)
DRV8874 KiCad kutuphanesinde yok; pin tablosu TI veri sayfasindan (SLVSF66),
bkz. docs/04-netlist.md.
"""

BW, BH, BR = 85.0, 56.0, 3.0
CUT = dict(x1=40.0, x2=57.0, depth=14.0, r=1.5)    # kamera/DSI kesiti - DOGRULA
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]
J1_PIN1 = (8.366, 51.641)                            # Gemstone 40-pin, pin 1 - DOGRULA

# Gemstone'un ust yuzundeki yuksek bloklar (shield bunlarin USTUNDEN gecer)
TALL = [("USB-A x3", 68.0, 20.0, 85.0, 52.0), ("RJ45", 60.0, 0.0, 85.0, 18.0)]

PARTS = []


def P(ref, value, fp, nets=None, side="F", mpn="", desc="", anchor="center"):
    PARTS.append(dict(ref=ref, value=value, fp=fp, nets=nets or {}, side=side,
                      mpn=mpn, desc=desc, anchor=anchor))


R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
XH = "Connector_JST:JST_XH_B{n}B-XH-A_1x0{n}_P2.50mm_Vertical"
TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
DRV_FP = "Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm_ThermalVias"


def R(ref, val, a, b, desc=""):
    P(ref, val, R0603, {"1": a, "2": b}, desc=desc)


def C(ref, val, a, b="GND", fp=C0603, desc=""):
    P(ref, val, fp, {"1": a, "2": b}, desc=desc)


# =============================================================================
# 40-pin Gemstone soketi - govde kartin ALTINDA (B yuzu), pin 1 Gemstone'un pin 1'i
# =============================================================================
HOST = {8: "HOST_TX",       # Gemstone TXD (GPIO-14) -> ESP32 RX (IO48)
        10: "HOST_RX",      # Gemstone RXD (GPIO-15) <- ESP32 TX (IO47)
        13: "ESTOP_STAT",   # ESP32 -> host, acil stop durumu
        37: "BUZZER"}       # host -> buzzer FET
J1_GND = [6, 9, 14, 20, 25, 30, 34, 39]
P("J1", "Gemstone 40P disi", "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical",
  {str(p): ("GND" if p in J1_GND else HOST.get(p, "")) for p in range(1, 41)},
  side="B", anchor="pin1", mpn="2x20 disi, >=16mm gecis (stacking)",
  desc="5V pinleri (2,4) BILEREK bos")

# =============================================================================
# ESP32-S3-WROOM-1U  (U.FL modulun ustunde - harici anten kablosu)
# =============================================================================
# Pin atamasi COGRAFYAYA gore (GPIO matrisi: LEDC/MCPWM/PCNT/UART her pine atanir):
#   sol kenar  -> sola/yukari giden: host UART (J1), acil stop butonu (J12), bumper, GPIO
#   alt sira   -> motor surucu sinyalleri (karti boydan boya gecer), LED, INA226 ALERT
#   sag kenar  -> enkoder, I2C, ESTOP_STAT; IPROPI ADC1 icin IO1/IO2'de kalir
ESP = {
    "1": "GND", "2": "+3V3", "3": "EN",
    "4": "HOST_RX", "5": "HOST_TX",                                   # IO4=TX -> host RX, IO5=RX
    "6": "ESTOP_LOOP", "7": "BUMP1", "8": "BUMP2",                    # IO6, IO7, IO15
    "9": "GPIO16", "10": "GPIO17", "11": "", "12": "",                # IO16, IO17 (J14); IO18, IO8 bos
    "13": "USB_DM", "14": "USB_DP",                                   # IO19, IO20
    "15": "", "16": "",                                               # IO3, IO46 strap - bos
    "17": "MA_PH", "18": "MA_EN", "19": "MB_PH", "20": "MB_EN",       # IO9..IO12
    "21": "DRV_nSLEEP", "22": "DRV_nFAULT", "23": "ESTOP_DRV",        # IO13, IO14, IO21
    "24": "LED_DATA", "25": "PWR_ALERT", "26": "",                    # IO47, IO48, IO45 strap
    "27": "BOOT_BTN",                                                 # IO0
    "28": "", "29": "", "30": "",                                     # IO35-37 (PSRAM) - bos
    "31": "ENC_A1", "32": "ENC_B1", "33": "ENC_A2", "34": "ENC_B2",  # IO38..IO41 (PCNT)
    "35": "I2C_SDA", "36": "I2C_SCL",                                 # IO42, IO44 (U0RXD)
    "37": "ESTOP_STAT",                                               # IO43 (U0TXD) -> host
    "38": "IPROPI_B", "39": "IPROPI_A",                               # IO2, IO1 (ADC1)
    "40": "GND", "41": "GND"}
P("U1", "ESP32-S3-WROOM-1U-N8R2", "RF_Module:ESP32-S3-WROOM-1U", ESP,
  mpn="ESP32-S3-WROOM-1U-N8R2", desc="N8R8 ALMA: IO35-37 kaybolur")
C("C3", "22u", "+3V3", fp=C0805, desc="3V3 bulk")
C("C4", "100n", "+3V3", desc="U1 pin 2 dekuplaj")
R("R3", "10k", "EN", "+3V3", "EN pull-up")
C("C14", "1u", "EN", desc="EN RC gecikmesi (zorunlu)")
P("SW1", "BOOT", "Button_Switch_SMD:SW_SPST_PTS810", {"1": "BOOT_BTN", "2": "GND"},
  mpn="PTS810 SJM 250 SMTR LFS")
P("SW2", "RESET", "Button_Switch_SMD:SW_SPST_PTS810", {"1": "EN", "2": "GND"},
  mpn="PTS810 SJM 250 SMTR LFS")

# --- USB-C (flaslama + ESP32 USB-Serial/JTAG) + ESD ---
P("J11", "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
  {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
   "A4": "+5V_USB", "A9": "+5V_USB", "B4": "+5V_USB", "B9": "+5V_USB",
   "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
   "A7": "USB_DM", "B7": "USB_DM", "A8": "", "B8": ""},
  mpn="GCT USB4105-GF-A", desc="flaslama / konsol")
P("U10", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
  {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "+5V_USB"},
  mpn="USBLC6-2SC6", desc="USB ESD")
R("R1", "5k1", "CC1", "GND")
R("R2", "5k1", "CC2", "GND")
P("D1", "B5819W", "Diode_SMD:D_SOD-123", {"1": "+5V", "2": "+5V_USB"},
  mpn="B5819W", desc="USB 5V -> +5V (pad1=K)")

# =============================================================================
# Guc girisi: XT60 -> F1 -> Q1 ters polarite -> RS1 shunt -> VSYS
# =============================================================================
P("J2", "XT60 2S LiPo", "Connector_AMASS:AMASS_XT60-F_1x02_P7.20mm_Vertical",
  {"1": "VBAT_RAW", "2": "GND"}, mpn="AMASS XT60-F", desc="6.0-8.4V; bataryanin karsiligi")
P("F1", "20A", "Fuse:Fuse_2512_6332Metric", {"1": "VBAT_RAW", "2": "VBAT_F"},
  mpn="Bel Fuse 0685P/2512 20A", desc="giris sigortasi")
P("Q1", "AO4407A", SO8,
  {"1": "VBAT", "2": "VBAT", "3": "VBAT", "4": "GND_GATE",
   "5": "VBAT_F", "6": "VBAT_F", "7": "VBAT_F", "8": "VBAT_F"},
  mpn="AO4407A", desc="ters polarite P-FET (D=giris, S=cikis)")
R("R5", "100k", "GND_GATE", "GND", "Q1 gate -> GND")
# 4 uclu (Kelvin) shunt: 1/4 akim uclari, 2/3 olcum uclari -> INA226'ya ayri netlerle
P("RS1", "2m 3W", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm",
  {"1": "VBAT", "2": "SNS_P", "3": "SNS_N", "4": "VSYS"},
  mpn="Vishay WSK2512 2mOhm", desc="Kelvin akim shuntu")
P("U5", "INA226", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
  {"1": "+3V3", "2": "+3V3", "3": "PWR_ALERT", "4": "I2C_SDA", "5": "I2C_SCL",
   "6": "+3V3", "7": "GND", "8": "SNS_N", "9": "SNS_N", "10": "SNS_P"},
  mpn="INA226AIDGSR", desc="I2C 0x45 (A0=A1=VS)")
C("C5", "100n", "+3V3")
R("R15", "10k", "PWR_ALERT", "+3V3")
P("J3", "GEMSTONE GUC", TERM2, {"1": "VSYS", "2": "GND"},
  mpn="KF301-2P 5.08", desc="Gemstone DC girisine pigtail")

# --- 5 V servo/mantik BEC: TPS563201 ---
P("U7", "TPS563201", "Package_TO_SOT_SMD:SOT-23-6",
  {"1": "GND", "2": "SW5V", "3": "VSYS", "4": "+5V_FB", "5": "VSYS", "6": "BOOT5V"},
  mpn="TPS563201DDCR", desc="5V/3A BEC")
C("C7", "10u 25V", "VSYS", fp=C0805)
C("C16", "100n 25V", "VSYS")
C("C13", "100n", "BOOT5V", "SW5V")
P("L1", "3u3", "Inductor_SMD:L_Sunlord_SWPA5040S", {"1": "SW5V", "2": "+5V"},
  mpn="SWPA5040S3R3MT", desc="Isat >= 4A")
R("R12", "56k", "+5V", "+5V_FB", "Vout = 0.768*(1+56/10) = 5.07V")
R("R13", "10k", "+5V_FB", "GND")
C("C6", "22u", "+5V", fp=C0805)
C("C15", "22u", "+5V", fp=C0805)

# --- 3V3 LDO ---
P("U6", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
  {"1": "+5V", "2": "GND", "3": "+5V", "4": "", "5": "+3V3"}, mpn="AP2112K-3.3TRG1")
C("C1", "10u", "+5V", fp=C0805)
C("C2", "10u", "+3V3", fp=C0805)

# =============================================================================
# Acil stop: Q2 high-side P-FET, VARSAYILAN KAPALI
#   Q2 gate VSYS'e cekili (R6) -> kapali.
#   Acmak icin: ESP32 ESTOP_DRV=1 VE harici NC buton (J12) kapali olmali.
#   ESP32 reset/olu -> R16 Q3'u kapatir. Buton basili/kablo kopuk -> Q3 source acik.
# =============================================================================
P("Q2", "AO4407A", SO8,
  {"1": "VSYS", "2": "VSYS", "3": "VSYS", "4": "ESTOP_GATE",
   "5": "VBAT_SW", "6": "VBAT_SW", "7": "VBAT_SW", "8": "VBAT_SW"},
  mpn="AO4407A", desc="acil stop kesici (S=VSYS, D=motor)")
R("R6", "100k", "ESTOP_GATE", "VSYS", "gate pull-up = varsayilan KAPALI")
P("Q3", "AO3400A", SOT23, {"1": "ESTOP_DRV", "2": "ESTOP_LOOP", "3": "ESTOP_GATE"},
  mpn="AO3400A")
R("R16", "100k", "ESTOP_DRV", "GND", "ESP32 reset -> motor kapali")
R("R17", "10k", "ESTOP_LOOP", "+3V3", "buton acik -> 3V3 (ESP32 okur)")
P("J12", "ACIL STOP (NC)", XH.format(n=2), {"1": "ESTOP_LOOP", "2": "GND"},
  mpn="JST B2B-XH-A", desc="NC buton; buton yoksa kopru tak")


# =============================================================================
# Motor suruculer: DRV8874 x2 (PH/EN modu: PMODE=GND; IMODE=GND)
# =============================================================================
def drv(ch):
    return {"1": f"M{ch}_EN", "2": f"M{ch}_PH", "3": "DRV_nSLEEP", "4": "DRV_nFAULT",
            "5": "+3V3", "6": f"IPROPI_{ch}", "7": "GND", "8": f"OUT{ch}1", "9": "GND",
            "10": f"OUT{ch}2", "11": "VBAT_SW", "12": f"VCP_{ch}", "13": f"CPH_{ch}",
            "14": f"CPL_{ch}", "15": "GND", "16": "GND", "17": "GND"}


P("U2", "DRV8874", DRV_FP, drv("A"), mpn="DRV8874PWPR", desc="motor A")
P("U3", "DRV8874", DRV_FP, drv("B"), mpn="DRV8874PWPR", desc="motor B")
for ch, cvcp, ccp, cvm, rip in (("A", "C22", "C24", "C9", "R7"), ("B", "C23", "C25", "C10", "R8")):
    C(cvcp, "100n 16V", f"VCP_{ch}", "VBAT_SW", fp=C0402, desc="VCP - VM")
    C(ccp, "22n 50V", f"CPH_{ch}", f"CPL_{ch}", fp=C0402, desc="CPH - CPL")
    C(cvm, "100n 50V", "VBAT_SW", fp=C0402, desc="VM dekuplaj")
    R(rip, "1k5", f"IPROPI_{ch}", "GND", "IPROPI: 3.3V ~ 4.9A")
R("R4", "10k", "DRV_nFAULT", "+3V3", "nFAULT pull-up")
P("C8", "100u 25V", "Capacitor_SMD:CP_Elec_6.3x7.7", {"1": "VBAT_SW", "2": "GND"},
  mpn="EEE-FK1E101P", desc="motor bulk")
P("J4", "MOTOR A", TERM2, {"1": "OUTA1", "2": "OUTA2"}, mpn="KF301-2P 5.08")
P("J5", "MOTOR B", TERM2, {"1": "OUTB1", "2": "OUTB2"}, mpn="KF301-2P 5.08")

# =============================================================================
# Enkoder: 5V hall -> 74LVC245 -> 3V3, pull-up dizisi (acik-kollektor enkoderler)
# =============================================================================
BUF = {"1": "+3V3", "2": "ENC_A1_5V", "3": "ENC_B1_5V", "4": "ENC_A2_5V", "5": "ENC_B2_5V",
       "6": "GND", "7": "GND", "8": "GND", "9": "GND", "10": "GND",
       "11": "", "12": "", "13": "", "14": "",
       "15": "ENC_B2", "16": "ENC_A2", "17": "ENC_B1", "18": "ENC_A1",
       "19": "GND", "20": "+3V3"}
P("U8", "74LVC245", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm", BUF,
  mpn="SN74LVC245APWR", desc="5V -> 3V3 tampon")
C("C11", "100n", "+3V3")
P("RN1", "4x10k", "Resistor_SMD:R_Array_Convex_4x0603",
  {"1": "ENC_A1_5V", "2": "ENC_B1_5V", "3": "ENC_A2_5V", "4": "ENC_B2_5V",
   "5": "+5V", "6": "+5V", "7": "+5V", "8": "+5V"}, mpn="CAY16-103J4LF")
P("J6", "ENKODER A", XH.format(n=4), {"1": "+5V", "2": "GND", "3": "ENC_A1_5V", "4": "ENC_B1_5V"},
  mpn="JST B4B-XH-A")
P("J7", "ENKODER B", XH.format(n=4), {"1": "+5V", "2": "GND", "3": "ENC_A2_5V", "4": "ENC_B2_5V"},
  mpn="JST B4B-XH-A")

# =============================================================================
# Servo: PCA9685 (0x40) + 2 x 8 kanal header (S / +5V / GND)
# =============================================================================
PCA = {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "GND", "24": "GND",   # A0..A5
       "14": "GND", "25": "GND", "23": "OE_N", "26": "I2C_SCL", "27": "I2C_SDA",
       "28": "+3V3"}
for i in range(8):
    PCA[str(6 + i)] = f"SERVO{i + 1}"           # LED0..LED7  -> pin 6..13
    PCA[str(15 + i)] = f"SERVO{i + 9}"          # LED8..LED15 -> pin 15..22
P("U4", "PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm", PCA,
  mpn="PCA9685PW", desc="16 kanal servo PWM")
C("C12", "100n", "+3V3")
R("R9", "10k", "OE_N", "GND", "cikislar her zaman acik")
R("R10", "4k7", "I2C_SDA", "+3V3")
R("R11", "4k7", "I2C_SCL", "+3V3")


def servo_nets(first):
    n = {}
    for i in range(8):
        n[str(3 * i + 1)] = f"SERVO{first + i}"
        n[str(3 * i + 2)] = "+5V"
        n[str(3 * i + 3)] = "GND"
    return n


P("J8A", "SERVO 1-8", "T3RS:Servo_3x08_P2.54mm", servo_nets(1), mpn="3x8 erkek header 2.54")
P("J8B", "SERVO 9-16", "T3RS:Servo_3x08_P2.54mm", servo_nets(9), mpn="3x8 erkek header 2.54")

# =============================================================================
# Durum LED'leri: SK6812MINI x4 (+5V) + 74AHCT1G125 seviye cevirici
#   SK6812MINI pinleri: 1=DOUT 2=VSS 3=DIN 4=VDD  (WS2812B'den FARKLI)
# =============================================================================
P("U9", "74AHCT1G125", "Package_TO_SOT_SMD:SOT-23-5",
  {"1": "GND", "2": "LED_DATA", "3": "GND", "4": "LED_DIN", "5": "+5V"},
  mpn="SN74AHCT1G125DBVR", desc="3V3 -> 5V veri")
C("C21", "100n", "+5V")
_led_in = ["LED_DIN", "LED_D1", "LED_D2", "LED_D3"]
for i in range(4):
    P(f"DS{i + 1}", "SK6812MINI", "LED_SMD:LED_SK6812MINI_PLCC4_3.5x3.5mm_P1.75mm",
      {"1": f"LED_D{i + 1}", "2": "GND", "3": _led_in[i], "4": "+5V"}, mpn="SK6812MINI")
    C(f"C{17 + i}", "100n", "+5V")

# =============================================================================
# Kullanici / harici
# =============================================================================
P("LS1", "BUZZER 5V", XH.format(n=2), {"1": "+5V", "2": "BUZZER_DRV"},
  mpn="JST B2B-XH-A", desc="harici manyetik buzzer")
P("Q4", "AO3400A", SOT23, {"1": "BUZZER", "2": "GND", "3": "BUZZER_DRV"}, mpn="AO3400A")
P("D2", "B5819W", "Diode_SMD:D_SOD-123", {"1": "+5V", "2": "BUZZER_DRV"},
  mpn="B5819W", desc="flyback (pad1=K)")
R("R14", "10k", "BUZZER", "GND", "host yokken sessiz")
P("J10", "QWIIC", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
  {"1": "GND", "2": "+3V3", "3": "I2C_SDA", "4": "I2C_SCL", "MP": "GND"},
  mpn="JST SM04B-SRSS-TB")
P("J13", "BUMPER", XH.format(n=3), {"1": "GND", "2": "BUMP1", "3": "BUMP2"},
  mpn="JST B3B-XH-A")
P("J14", "GPIO", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
  {"1": "+3V3", "2": "GPIO16", "3": "GPIO17", "4": "GND"}, mpn="1x4 erkek 2.54")

for i in range(len(HOLES)):
    P(f"MH{i + 1}", "M2.5", "MountingHole:MountingHole_2.7mm_M2.5", {})

# =============================================================================
# YERLESIM   ref: (x, y, rot)
#   sol-alt   : guc girisi (XT60 -> sigorta -> Q1 -> shunt) + 5V BEC + 3V3 LDO
#   sol       : USB-C, Gemstone guc klemensi, buzzer / acil stop konnektoru
#   sol-ust   : ESP32-S3-WROOM-1U
#   orta      : BOOT/RESET, bumper, servo header x2, PCA9685, LED sirasi
#   sag       : motor suruculer + klemensler, acil stop FET, enkoder tamponu
#   ust kenar : 40-pin soket (Gemstone dayatir), Qwiic
# =============================================================================
POS = {
    "J1": (J1_PIN1[0], J1_PIN1[1], 270),
    "MH1": (*HOLES[0], 0), "MH2": (*HOLES[1], 0), "MH3": (*HOLES[2], 0), "MH4": (*HOLES[3], 0),
    # ESP32 + cevresi
    "U1": (18.8, 39.6, 0),
    "C4": (8.2, 47.6, 90), "R3": (8.2, 44.5, 90), "C14": (8.2, 41.4, 90),
    "SW1": (32.6, 42.0, 0), "SW2": (32.6, 37.6, 0),
    "J12": (3.9, 45.1, 90), "LS1": (3.9, 36.6, 90),
    # USB
    "J11": (4.2, 26.4, 270), "U10": (10.6, 26.2, 90), "R1": (10.6, 22.6, 0),
    "R2": (10.6, 20.9, 0), "D1": (15.2, 27.9, 180),
    # guc girisi
    "J2": (15.3, 5.0, 180), "F1": (25.9, 5.0, 90), "Q1": (31.6, 3.5, 180), "R5": (33.6, 7.3, 0),
    "RS1": (37.6, 5.0, 90), "U5": (33.0, 12.7, 0), "C5": (38.0, 12.7, 90),
    "R15": (38.0, 16.6, 90), "J3": (4.4, 15.6, 270),
    # 5V BEC + 3V3 LDO
    "U7": (15.0, 13.0, 180), "C7": (10.6, 12.8, 90), "C16": (15.0, 15.6, 180),
    "C13": (15.0, 10.4, 0), "L1": (20.6, 13.0, 0), "R12": (13.6, 18.0, 180),
    "R13": (13.6, 19.7, 0), "C15": (24.7, 13.0, 90), "C6": (26.9, 13.0, 90),
    "U6": (20.6, 21.6, 0), "C1": (20.6, 18.0, 0), "C2": (20.6, 25.0, 180), "C3": (24.8, 25.0, 90),
    # buzzer surucu
    "Q4": (25.6, 18.6, 0), "D2": (25.6, 21.6, 0), "R14": (26.6, 15.9, 0),
    # orta
    "U9": (31.6, 17.4, 0), "C21": (35.4, 17.4, 90),
    "R10": (32.6, 21.0, 0), "R11": (32.6, 22.7, 0), "J13": (32.7, 29.2, 90),
    "U4": (47.4, 26.4, 90), "C12": (40.7, 29.4, 180), "R9": (40.4, 26.4, 90),
    "J8A": (47.4, 44.2, 0), "J8B": (47.4, 35.2, 0),
    "DS1": (43.4, 16.6, 180), "DS2": (49.2, 16.6, 180), "DS3": (55.0, 16.6, 180), "DS4": (60.8, 16.6, 180),
    "C17": (43.4, 19.6, 0), "C18": (49.2, 19.6, 0), "C19": (55.0, 19.6, 0), "C20": (60.8, 19.6, 0),
    # acil stop mantigi
    "Q3": (60.6, 24.1, 0), "R6": (60.6, 27.1, 0), "R16": (60.6, 28.8, 0), "R17": (60.6, 30.5, 0),
    "J14": (60.6, 37.0, 0), "R4": (60.6, 44.5, 0),
    # motor
    "U2": (73.4, 18.0, 90), "U3": (73.4, 6.0, 90),
    "C22": (73.9, 24.1, 0), "C24": (72.6, 22.7, 180), "R7": (67.4, 17.0, 0), "C9": (76.0, 24.4, 90),
    "C23": (73.9, 12.1, 0), "C25": (72.6, 10.7, 180), "R8": (67.4, 5.4, 0), "C10": (75.1, 13.2, 0),
    "J4": (80.95, 17.9, 90), "J5": (80.25, 6.9, 90),
    "Q2": (67.4, 25.1, 90), "C8": (69.4, 32.5, 0),
    # enkoder
    "U8": (73.2, 40.1, 90), "C11": (73.2, 45.3, 0), "RN1": (66.4, 40.1, 180),
    "J6": (81.6, 43.7, 90), "J7": (81.6, 30.2, 90),
    "J10": (69.9, 52.5, 180),
}

for _p in PARTS:
    _p["x"], _p["y"], _p["rot"] = POS[_p["ref"]]

# termal via dizili pedler duzleme dogrudan baglanir; sik (2.54) header pinlerinde
# termal kollar 45 derece (komsu pinlerin arasindan gecsin diye)
PAD_FULL = {"U1": ["41"], "U2": ["17"], "U3": ["17"], "J11": ["S1"]}
SPOKE45 = ["J1", "J8A", "J8B", "J6", "J7", "J13", "J14"]

# =============================================================================
# Net siniflari - otomatik yonlendirici icin. Yuksek akim yollari (pour + elle
# cizilen genis yollar) sinif genisliginden bagimsizdir; burasi ince pinlere
# (0.5 / 0.65 mm adim) girebilecek genislikte tutuldu.
# =============================================================================
NETCLASS = {
    "Guc": dict(track=0.3, clearance=0.2, via=0.6, drill=0.3,
                nets=["VBAT_RAW", "VBAT_F", "VBAT", "VSYS", "VBAT_SW",
                      "OUTA1", "OUTA2", "OUTB1", "OUTB2"]),
    "Ray": dict(track=0.25, clearance=0.15, via=0.5, drill=0.25,
                nets=["+5V", "+3V3", "GND", "SW5V", "+5V_USB"]),
    # USB-C 0.5 mm adimli pedler (0.2 mm bosluk) arasindan cikabilsin
    "USB": dict(track=0.15, clearance=0.1, via=0.5, drill=0.25, nets=["USB_DP", "USB_DM"]),
}
DEFAULT = dict(track=0.15, clearance=0.15, via=0.5, drill=0.25)

# =============================================================================
# GUC DAGITIMI
#   In2.Cu bolgeleri (aralarinda 0.4 mm bosluk):
#     VSYS    sol-alt guc bolgesi (J3, BEC girisi, shunt cikisi)
#     +5V     BEC cikisindan servo header'larina, LED'lere, enkoder bolgesine
#     +3V3    ESP32 bolgesi (sol-ust)
#     VBAT_SW motor bolgesi (sag-alt)
#   Yuksek akim: F.Cu dokumleri + elle cizilmis yollar. VSYS sag tarafa (Q2'ye)
#   B.Cu'da 2 mm govdeyle, kamera kesitinin ustunden (y = 15.4) tasinir.
# =============================================================================
IN2_SPLIT = [
    ("VSYS", [(0, 0), (39.8, 0), (39.8, 11.0), (17.4, 11.0), (17.4, 20.6), (0, 20.6)]),
    ("+5V", [(17.8, 11.4), (39.8, 11.4), (39.8, 14.2), (64.0, 14.2), (64.0, 36.0), (78.0, 36.0),
             (78.0, 23.4), (85, 23.4), (85, 56), (29.6, 56), (29.6, 22.8), (23.4, 22.8),
             (23.4, 23.8), (17.8, 23.8)]),
    ("+3V3", [(0, 21.4), (17.4, 21.4), (17.4, 24.2), (23.0, 24.2), (23.0, 23.2), (29.2, 23.2),
              (29.2, 56), (0, 56)]),
    ("VBAT_SW", [(57.2, 0), (85, 0), (85, 23.0), (77.6, 23.0), (77.6, 35.6), (64.4, 35.6),
                 (64.4, 13.8), (57.2, 13.8)]),
]

def _drv_pours(dy, ch, jx, j1, j2):
    """DRV8874 cikis + VM dokumleri (U3: dy=0, U2: dy=12). (jx, j1/j2) = klemens pedleri.
    Ince pinlere (0.65 mm adim) dolgu motoru komsu pinlerden bosluk birakarak girer."""
    return [
        (f"OUT{ch}1", [(75.45, 1.4 + dy), (jx + 1.65, 1.4 + dy), (jx + 1.65, max(4.95 + dy, j1 + 1.6)),
                       (76.4, max(4.95 + dy, j1 + 1.6)), (76.4, 4.1 + dy), (75.45, 4.1 + dy)]),
        (f"OUT{ch}2", [(74.85, 8.0 + dy), (75.25, 8.0 + dy), (75.25, 9.88 + dy), (jx - 1.55, 9.88 + dy),
                       (jx - 1.55, j2 - 1.55), (jx + 1.55, j2 - 1.55), (jx + 1.55, 11.4 + dy),
                       (74.85, 11.4 + dy)]),
        ("VBAT_SW", [(x, y + dy) for x, y in ((74.05, 8.0), (74.6, 8.0), (74.6, 11.6), (76.4, 11.6),
                                              (76.4, 12.55), (74.0, 12.55), (74.0, 8.0))]),
    ]


J5_PADS = (80.25, 4.36, 9.44)       # klemens ped merkezleri (x, ped1 y, ped2 y)
J4_PADS = (80.95, 15.36, 20.44)

F_POURS = [
    ("VBAT_RAW", [(15.6, 0.6), (27.75, 0.6), (27.75, 3.35), (22.3, 3.35), (22.3, 8.3), (15.6, 8.3)]),
    ("VBAT_F", [(22.8, 6.3), (28.05, 6.3), (28.05, 0.6), (30.8, 0.6), (30.8, 9.4), (22.8, 9.4)]),
    # RS1 olcum pedleri (SNS_P sag-alt, SNS_N sol-ust) dokumlerin disinda kalsin
    ("VBAT", [(32.9, 0.6), (38.15, 0.6), (38.15, 4.5), (32.9, 4.5)]),
    ("VSYS", [(37.2, 6.2), (39.6, 6.2), (39.6, 10.6), (37.2, 10.6)]),
    ("+5V", [(21.6, 10.6), (28.2, 10.6), (28.2, 12.85), (23.3, 12.85), (23.3, 16.3), (21.6, 16.3)]),
    ("VSYS", [(15.4, 13.6), (17.4, 13.6), (17.4, 16.4), (15.4, 16.4)]),          # U7 VIN + C16
    ("VSYS", [(62.9, 20.8), (68.65, 20.8), (68.65, 23.9), (62.9, 23.9)]),
    ("VBAT_SW", [(64.6, 26.25), (70.35, 26.25), (70.35, 29.1), (68.6, 29.1), (68.6, 34.2),
                 (64.6, 34.2)]),
] + _drv_pours(0.0, "B", *J5_PADS) + _drv_pours(12.0, "A", *J4_PADS)


def _spine(net, w, *pts):
    return dict(net=net, w=w, pts=list(pts))


def _drv_spines(dy, ch, jx, j1, j2):
    o1, o2 = f"OUT{ch}1", f"OUT{ch}2"
    return [
        _spine(o1, 0.4, (75.67, 3.14 + dy), (76.6, 3.14 + dy)),
        _spine(o1, 1.0, (76.6, 3.14 + dy), (jx, j1)),
        _spine(o2, 0.4, (75.03, 8.86 + dy), (75.03, 10.6 + dy)),
        _spine(o2, 0.8, (75.43, 10.6 + dy), (jx, 10.6 + dy)),   # bas: VM omurgasindan 0.2+
        _spine(o2, 1.0, (jx, 10.6 + dy), (jx, j2)),
        _spine("VBAT_SW", 0.3, (74.38, 8.86 + dy), (74.38, 12.1 + dy)),
        _spine("VBAT_SW", 0.4, (74.38, 12.1 + dy), (75.95, 12.1 + dy)),
    ]


# Dokum "omurgalari": her F.Cu guc dokumunun ortasinda ayni netten kilitli yol.
# Freerouting dokumleri diger netler icin engel saymiyor (icinden yol geciriyor);
# sabit yollari ise engel sayar. KiCad'de dokumu guclendiren gercek bakirdir.
SPINES = [
    _spine("VBAT_RAW", 1.6, (18.9, 2.1), (25.9, 2.1)),
    _spine("VBAT_F", 1.0, (25.9, 7.9), (29.12, 7.9), (29.12, 1.59)),
    _spine("VBAT", 1.0, (34.08, 2.86), (36.97, 2.02)),
    _spine("VSYS", 0.8, (38.23, 7.98), (38.6, 9.7)),
    _spine("VSYS", 0.8, (63.4, 21.4), (64.2, 22.0), (68.03, 22.0)),
    _spine("VBAT_SW", 0.8, (65.5, 27.58), (69.31, 27.58)),
    _spine("VBAT_SW", 1.0, (66.3, 27.58), (66.3, 32.5)),
    _spine("+5V", 0.8, (22.45, 12.05), (26.9, 12.05)),
    _spine("VSYS", 0.5, (16.14, 13.95), (16.9, 15.0), (16.9, 15.75)),
] + _drv_spines(0.0, "B", *J5_PADS) + _drv_spines(12.0, "A", *J4_PADS)

POWER_TRACKS = SPINES + (
    # VSYS -> Q2 govdesi yalnizca B.Cu'da ve kamera kesitinin hemen ustunden: F.Cu
    # tamamen serbest, B.Cu'da da karti bolen bir duvar olusturmuyor (alti bos serit)
    [dict(net="VSYS", w=2.0, layer="B", pts=[(38.6, 9.7), (38.6, 15.4), (63.0, 15.4), (63.0, 21.4),
                                              (63.4, 21.4)]),
     # BEC geri besleme ust direnci -> +5V (C1)
     dict(net="+5V", w=0.3, pts=[(14.42, 18.0), (19.65, 18.0)]),
     # USB 5V (D1 katodu) -> LDO girisi: D1 +3V3 bolgesinde, +5V'a ayri yol
     dict(net="+5V", w=0.4, pts=[(16.85, 27.9), (17.6, 27.15), (17.6, 23.3), (18.35, 22.55),
                                 (19.46, 22.55)]),
     # U3 VM dekuplaji (C10) -> VM omurgasi
     dict(net="VBAT_SW", w=0.3, pts=[(74.62, 13.2), (74.62, 12.1)]),
     # +3V3 omurgasi: LDO cikisindan (C3) orta bolgeye; +3V3 duzlemi yalnizca solda,
     # sagdaki tuketiciler (PCA9685, INA226, 74LVC245, VREF, I2C, Qwiic) buna baglanir.
     # B.Cu'da: suruculere giden sinyaller F.Cu'da hem bunun hem VSYS govdesinin
     # ustunden via'siz gecebilir.
     # LDO cikisi: U6.5 -> C2 (cikis kondansatoru) -> C3 -> omurga basi / duzlem viasi
     dict(net="+3V3", w=0.4, pts=[(21.74, 22.55), (21.55, 25.0), (22.5, 24.05), (24.8, 24.05)]),
     dict(net="+3V3", w=0.5, pts=[(24.8, 24.05), (25.3, 23.8), (26.4, 23.8)]),
     dict(net="+3V3", w=0.4, layer="B", pts=[(26.4, 23.8), (36.5, 23.8), (38.9, 21.4), (58.0, 21.4)]),
     # omurga ucu -> sag bolge (R17 uzerinden enkoder tamponu, VREF, Qwiic, J14)
     dict(net="+3V3", w=0.3, layer="B", pts=[(58.0, 21.4), (58.0, 29.5), (59.0, 30.5), (62.3, 30.5)]),
     dict(net="+3V3", w=0.3, pts=[(61.42, 30.5), (62.3, 30.5)]),
     # U1 3V3 dekuplaji: C4 pin 1 (3V3) U1 pin 2'nin, C4 pin 2 (GND) U1 pin 1'in yaninda
     dict(net="+3V3", w=0.3, pts=[(10.05, 46.97), (8.2, 46.82), (7.1, 46.82)]),
     dict(net="GND", w=0.3, pts=[(10.05, 48.23), (8.2, 48.38)]),
     # PCA9685 VDD dekuplaji; omurgadan B.Cu kolla beslenir
     dict(net="+3V3", w=0.3, pts=[(41.475, 29.26), (43.17, 29.26)]),
     dict(net="+3V3", w=0.3, pts=[(41.3, 28.3), (41.475, 29.26)]),
     dict(net="+3V3", w=0.3, layer="B", pts=[(41.3, 21.4), (41.3, 28.3)]),
     # I2C pull-up'lari (R10, R11) dogrudan omurgaya
     dict(net="+3V3", w=0.3, pts=[(33.42, 21.0), (33.42, 23.8)]),
     # LED +5V: pedlerin altinda kesit + VSYS govdesi var, via konamaz. DS1..DS4'un +5V
     # pinleri kesitin ustundeki F.Cu raydan birlesir, ray DS1'in solundan C17'ye cikar
     dict(net="+5V", w=0.3, pts=[(41.65, 15.72), (40.4, 15.72), (40.4, 18.9), (41.1, 19.6),
                                 (42.62, 19.6)]),
     dict(net="+5V", w=0.3, pts=[(41.65, 15.72), (41.65, 14.8), (59.05, 14.8), (59.05, 15.72)]),
     dict(net="+5V", w=0.3, pts=[(47.45, 14.8), (47.45, 15.72)]),
     dict(net="+5V", w=0.3, pts=[(53.25, 14.8), (53.25, 15.72)]),
     # EN pull-up (R3) 3V3 ucu dogrudan C4'e
     dict(net="+3V3", w=0.3, pts=[(8.2, 45.33), (8.2, 46.82)]),
     # INA226 A0 = A1 = VS (0x45): pinler soldan via ile B.Cu'ya, oradan +3V3 omurgasina
     dict(net="+3V3", w=0.2, pts=[(30.8, 13.7), (30.8, 13.2)]),
     dict(net="+3V3", w=0.2, pts=[(30.8, 13.45), (29.5, 13.45)]),
     dict(net="+3V3", w=0.25, layer="B", pts=[(29.5, 13.45), (29.5, 23.8)]),
     # USBLC6 GND: pedin cevresi USB yollariyla cevrili, via govdenin altinda
     dict(net="GND", w=0.3, pts=[(10.6, 25.06), (10.6, 26.2)])]
)

POWER_VIAS = [
    # (36.5, 9.7) YOK: B.Cu'daki VBAT Kelvin yolu x=36.4'ten geciyor
    dict(net="VSYS", at=[(37.6, 9.7), (38.6, 9.7), (63.4, 21.4), (63.4, 22.6)]),
    dict(net="VBAT_SW", at=[(65.3, 29.9), (66.3, 29.9), (67.3, 29.9),
                            (65.3, 30.8), (66.3, 30.8), (67.3, 30.8)]),
    dict(net="VBAT_SW", at=[(75.2, 12.1), (75.95, 12.1), (75.2, 24.1), (75.95, 24.1)],
         size=0.6, drill=0.3),
    dict(net="+5V", at=[(25.8, 12.0), (23.6, 12.0), (22.45, 15.75)]),
    dict(net="VSYS", at=[(16.9, 15.75)], size=0.6, drill=0.3),
    dict(net="+3V3", at=[(7.1, 46.82), (26.4, 23.8), (29.5, 13.45), (41.3, 28.3),
                         (33.42, 23.8), (62.3, 30.5)], size=0.5, drill=0.25),
    dict(net="+5V", at=[(41.1, 19.6)], size=0.5, drill=0.25),
    dict(net="GND", at=[(10.6, 26.2)], size=0.5, drill=0.25),
]

# (metin, x, y, boyut, kalinlik[, katman])  - katman yoksa F.SilkS
SILK = [
    ("SERVO 1-8   S + -", 36.9, 49.0, 0.8, 0.13),
    ("9-16", 36.35, 30.2, 0.7, 0.12),
    ("MOTOR A", 76.6, 23.4, 0.8, 0.13),
    ("MOTOR B", 70.8, 0.55, 0.6, 0.1),
    ("2S 6-8.4V", 7.2, 9.75, 0.6, 0.1),
    ("ENK A", 78.3, 50.6, 0.7, 0.12),
    ("ENK B", 78.3, 36.4, 0.7, 0.12),
    ("QWIIC", 74.2, 49.5, 0.7, 0.12),
]
