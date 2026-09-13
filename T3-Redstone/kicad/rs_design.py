"""T3-Redstone - devre tanimi, yerlesim ve netlist."""
from rs_lib import *

BW, BH, BR = 85.0, 56.0, 3.0
CUT = dict(x1=40.0, x2=57.0, depth=14.0, r=1.5)   # kamera/DSI kesiti - DOGRULA
HOLES = [(3.5,3.5),(61.5,3.5),(3.5,52.5),(61.5,52.5)]
J1_PIN1 = (8.366, 51.641)

# --------------------------------------------------------------------- netler
# 40-pin header uzerinden host'a giden 4 sinyal + guc
HOST = {8:"HOST_TX", 10:"HOST_RX", 13:"ESTOP_STAT", 37:"BUZZER"}
GND_PINS_J1 = [6,9,14,20,25,30,34,39]

def j1_nets():
    n = {}
    for p in range(1,41):
        if p in HOST: n[str(p)] = HOST[p]
        elif p in GND_PINS_J1: n[str(p)] = "GND"
        else: n[str(p)] = ""           # kullanilmayan pinler bosta - takima kalir
    return n

# ESP32-S3-WROOM-1U pad -> net  (pad numaralari veri sayfasindan)
ESP = {
 "1":"GND","2":"+3V3","3":"EN","4":"MA_PH","5":"MA_EN","6":"MB_PH","7":"MB_EN",
 "8":"DRV_nSLEEP","9":"DRV_nFAULT","10":"ENC_B1","11":"ENC_A2","12":"ENC_A1",
 "13":"USB_DM","14":"USB_DP","15":"BOOT_STRAP","16":"","17":"ENC_B2","18":"GPIO10",
 "19":"GPIO11","20":"SPARE1","21":"SPARE2","22":"SPARE3","23":"ESTOP_DRV","24":"HOST_TX",
 "25":"HOST_RX","26":"","27":"BOOT_BTN","28":"I2C_SCL","29":"BUMP2","30":"BUMP1",
 "31":"LED_DATA","32":"ESTOP_BTN","33":"SPARE4","34":"I2C_SDA","35":"I2C_SCL_X",
 "36":"DBG_RX","37":"DBG_TX","38":"IPROPI_B","39":"IPROPI_A","40":"GND","41":"GND"}
# not: 34=IO41=SDA, 35=IO42=SCL. 28=IO35 yanlis atanmasin diye duzeltiliyor:
ESP["28"]="SPARE5"; ESP["35"]="I2C_SCL"; ESP["34"]="I2C_SDA"
ESP["12"]="ENC_A1"; ESP["10"]="ENC_B1"; ESP["11"]="ENC_A2"; ESP["17"]="ENC_B2"
ESP["20"]="ESTOP_STAT"        # host bu pini J1-13'ten okur

# DRV8874 HTSSOP-16: 1=IPROPI 2=nSLEEP 3=EN/IN1 4=PH/IN2 5=nFAULT 6=GND 7=VREF 8=MODE
#                    9=OUT2 10=PGND 11=PGND 12=OUT2 13=OUT1 14=VM 15=VM 16=OUT1
def drv(ch):
    return {"1":f"IPROPI_{ch}","2":"DRV_nSLEEP","3":f"M{ch}_EN","4":f"M{ch}_PH",
            "5":"DRV_nFAULT","6":"GND","7":"+3V3","8":"GND",
            "9":f"OUT{ch}2","10":"GND","11":"GND","12":f"OUT{ch}2",
            "13":f"OUT{ch}1","14":"VBAT_SW","15":"VBAT_SW","16":f"OUT{ch}1","EP":"GND"}

# PCA9685 TSSOP-28: 1=A0 2=A1 3=A2 4=A3 5=A4 6=LED0..  asagida sadece guc/kontrol
# PCA9685 TSSOP-28: 1-6=A0..A5, 7-13=LED0..6, 14=VSS, 15-23=LED7..15,
# 24=OE_N, 25=EXTCLK, 26=SCL, 27=SDA, 28=VDD
PCA = {str(p):"GND" for p in range(1,7)}          # adres 0x40
PCA.update({"14":"GND","24":"OE_N","25":"GND","26":"I2C_SCL","27":"I2C_SDA","28":"+3V3"})
for i,p in enumerate(range(7,14)):  PCA[str(p)] = f"SERVO{i+1}"     # LED0..6  -> 1..7
for i,p in enumerate(range(15,24)): PCA[str(p)] = f"SERVO{i+8}"     # LED7..15 -> 8..16

# INA226 VSSOP-10: 1=IN+ 2=IN- 3=ALERT 4=GND 5=SCL 6=SDA 7=A0 8=A1 9=VBUS 10=VS
INA = {"1":"VBAT","2":"VSYS","3":"PWR_ALERT","4":"GND","5":"I2C_SCL",
       "6":"I2C_SDA","7":"+3V3","8":"GND","9":"VSYS","10":"+3V3"}

# 74LVC245 TSSOP-20: 1=DIR 2..9=A1..A8 10=GND 11..18=B8..B1 19=OE_N 20=VCC
BUF = {"1":"+3V3","10":"GND","19":"GND","20":"+3V3",
       "2":"ENC_A1_5V","3":"ENC_B1_5V","4":"ENC_A2_5V","5":"ENC_B2_5V",
       "6":"GND","7":"GND","8":"GND","9":"GND",
       "18":"ENC_A1","17":"ENC_B1","16":"ENC_A2","15":"ENC_B2",
       "14":"","13":"","12":"","11":""}

# ---------------------------------------------------------------- komponentler
# (ref, deger, uretici, args, x, y, rot, netmap, katman-ustu-yazi)
C = []
def add(ref,val,fp,args,x,y,rot=0,nets=None,desc=""):
    C.append(dict(ref=ref,val=val,fp=fp,args=args,x=x,y=y,rot=rot,nets=nets or {},desc=desc))

# --- 40-pin disi soket (ust kenar) ---
add("J1","GEMSTONE_40P_DISI",header,(20,2),J1_PIN1[0],J1_PIN1[1],0,j1_nets(),"Gemstone 40-pin")

# --- ESP32 bolgesi (sol-orta) ---
add("U1","ESP32-S3-WROOM-1U",wroom1u,(),17.0,33.0,0,ESP,"MCU")
add("J9","U.FL ANT",ufl,(),3.0,33.0,0,{"1":"ANT","2":"GND"},"harici anten")
add("J11","USB-C",usbc_16,(),3.8,46.0,90,
    {"A1":"GND","B12":"GND","A4":"+5V_USB","B4":"+5V_USB","A9":"+5V_USB","B9":"+5V_USB",
     "A6":"USB_DP","A7":"USB_DM","B6":"USB_DP","B7":"USB_DM",
     "A5":"CC1","B5":"CC2","A12":"GND","B1":"GND","S1":"GND","S2":"GND"},"flaslama")
add("SW1","BOOT",tact_smd,(),31.0,45.0,0,{"1":"BOOT_BTN","2":"BOOT_BTN","3":"GND","4":"GND"})
add("SW2","RESET",tact_smd,(),31.0,40.0,0,{"1":"EN","2":"EN","3":"GND","4":"GND"})
add("U6","AP2112K-3.3",sot23,(5,),31.0,34.0,0,{"1":"+5V","2":"GND","3":"+5V","4":"","5":"+3V3"})
add("C1","10u",chip,("0805",),34.5,34.0,90,{"1":"+5V","2":"GND"})
add("C2","10u",chip,("0805",),34.5,31.5,90,{"1":"+3V3","2":"GND"})
add("C3","22u",chip,("0805",),28.0,26.0,0,{"1":"+3V3","2":"GND"})
add("C4","100n",chip,("0603",),28.0,23.5,0,{"1":"+3V3","2":"GND"})
add("D1","SS14 SOD123",chip,("0805",),8.0,47.0,0,{"1":"+5V_USB","2":"+5V"},"USB 5V OR")
add("R1","5k1",chip,("0603",),8.0,44.0,0,{"1":"CC1","2":"GND"})
add("R2","5k1",chip,("0603",),8.0,42.0,0,{"1":"CC2","2":"GND"})
add("R3","10k",chip,("0603",),35.0,45.0,0,{"1":"EN","2":"+3V3"})
add("R4","10k",chip,("0603",),35.0,43.0,0,{"1":"DRV_nFAULT","2":"+3V3"})

# --- guc girisi (sol-alt) ---
add("J2","XT60 2S LiPo",xt60,(),10.0,6.0,0,{"1":"VBAT_RAW","2":"GND"},"6.0-8.4V")
add("F1","20A",chip,("2512",),20.0,6.0,0,{"1":"VBAT_RAW","2":"VBAT_F"},"sigorta")
add("Q1","P-MOSFET",sop,(8,1.27,5.4,1.5,0.6,5.0,4.0),26.0,6.0,180,
    {"1":"VBAT","2":"VBAT","3":"VBAT","4":"GND_GATE","5":"VBAT_F","6":"VBAT_F","7":"VBAT_F","8":"VBAT_F"},
    "ters polarite P-FET")
add("R5","100k",chip,("0603",),26.0,2.5,0,{"1":"GND_GATE","2":"GND"})
add("RS1","2m 2W",chip,("2512",),34.0,6.0,0,{"1":"VBAT","2":"VSYS"},"shunt")
add("U5","INA226",sop,(10,0.5,4.4,1.2,0.3,3.0,3.0),34.0,2.0,0,INA,"batarya olcer")
add("C5","100n",chip,("0603",),38.0,2.0,0,{"1":"+3V3","2":"GND"})
add("J3","GEMSTONE GUC",terminal,(2,),22.0,16.0,0,{"1":"VSYS","2":"GND"},"klemense pigtail")
add("Q2","P-FET ESTOP",sop,(8,1.27,5.4,1.5,0.6,5.0,4.0),38.0,18.0,180,
    {"1":"VBAT_SW","2":"VBAT_SW","3":"VBAT_SW","4":"ESTOP_GATE","5":"VSYS","6":"VSYS","7":"VSYS","8":"VSYS"},
    "acil stop kesici - high side")
add("Q3","N-FET SOT23",sot23,(3,0.95,2.6,1.0,0.6),43.0,15.0,0,
    {"1":"ESTOP_DRV","2":"GND","3":"ESTOP_GATE"},"gate surucu")
add("R6","100k",chip,("0603",),34.5,15.0,0,{"1":"ESTOP_GATE","2":"VSYS"},"gate pull-up = arizada KAPALI")
add("U7","TPS563201 5V",sot23,(6,),30.0,20.0,0,
    {"1":"GND","2":"SW5V","3":"VSYS","4":"+5V_FB","5":"VSYS","6":"BOOT5V"},"servo BEC")
add("C13","100n",chip,("0603",),27.0,22.5,0,{"1":"BOOT5V","2":"SW5V"})
add("R12","68k",chip,("0603",),33.0,17.0,0,{"1":"+5V","2":"+5V_FB"})
add("R13","10k",chip,("0603",),33.0,14.5,0,{"1":"+5V_FB","2":"GND"})
add("L1","4u7",chip,("1206",),30.0,17.0,0,{"1":"SW5V","2":"+5V"})
add("C6","22u",chip,("0805",),34.0,20.0,0,{"1":"+5V","2":"GND"})
add("C7","10u",chip,("0805",),26.0,20.0,0,{"1":"VSYS","2":"GND"})

# --- motor surucu (sag) ---
add("U2","DRV8874 A",sop,(16,0.65,5.2,1.5,0.4,5.0,5.0,(3.0,3.0)),74.0,38.0,0,drv("A"),"motor A")
add("U3","DRV8874 B",sop,(16,0.65,5.2,1.5,0.4,5.0,5.0,(3.0,3.0)),74.0,28.0,0,drv("B"),"motor B")
add("C8","100u",chip,("1206",),68.0,33.0,90,{"1":"VBAT_SW","2":"GND"})
add("C9","100n",chip,("0603",),79.0,38.0,90,{"1":"VBAT_SW","2":"GND"})
add("C10","100n",chip,("0603",),79.0,28.0,90,{"1":"VBAT_SW","2":"GND"})
add("R7","1k5",chip,("0603",),68.0,40.0,0,{"1":"IPROPI_A","2":"GND"})
add("R8","1k5",chip,("0603",),68.0,26.0,0,{"1":"IPROPI_B","2":"GND"})
add("J4","MOTOR A",terminal,(2,),76.0,20.0,0,{"1":"OUTA1","2":"OUTA2"})
add("J5","MOTOR B",terminal,(2,),76.0,8.0,0,{"1":"OUTB1","2":"OUTB2"})

# --- enkoder (sag-ust) ---
add("U8","74LVC245",sop,(20,0.65,6.4,1.5,0.4,6.5,4.4),66.0,45.0,0,BUF,"5V->3V3 tampon")
add("J6","ENKODER A",jst_xh,(4,),61.0,52.0,0,
    {"1":"+5V","2":"GND","3":"ENC_A1_5V","4":"ENC_B1_5V"})
add("J7","ENKODER B",jst_xh,(4,),74.0,52.0,0,
    {"1":"+5V","2":"GND","3":"ENC_A2_5V","4":"ENC_B2_5V"})
add("C11","100n",chip,("0603",),66.0,41.0,0,{"1":"+3V3","2":"GND"})

# --- servo (orta) ---
add("U4","PCA9685",sop,(28,0.65,7.8,1.5,0.4,9.7,4.4),40.0,20.0,0,PCA,"16 kanal servo")
add("C12","100n",chip,("0603",),46.0,20.0,0,{"1":"+3V3","2":"GND"})
add("R9","10k",chip,("0603",),46.0,17.5,0,{"1":"OE_N","2":"GND"})
add("J8A","SERVO 1-8",header,(8,3),30.5,39.0,0,
    {**{str(1+3*i):f"SERVO{i+1}" for i in range(8)},
     **{str(2+3*i):"+5V" for i in range(8)}, **{str(3+3*i):"GND" for i in range(8)}})
add("J8B","SERVO 9-16",header,(8,3),30.5,31.0,0,
    {**{str(1+3*i):f"SERVO{i+9}" for i in range(8)},
     **{str(2+3*i):"+5V" for i in range(8)}, **{str(3+3*i):"GND" for i in range(8)}})

# --- durum / kullanici ---
for i,(x,y) in enumerate([(3.0,26.0),(3.0,22.0),(3.0,18.0),(3.0,14.0)]):
    nin = "LED_DATA" if i==0 else f"LED_D{i}"
    nout= f"LED_D{i+1}"
    add(f"DS{i+1}","WS2812B",chip,("5050",),x,y,0,{"1":nin,"2":nout})
add("LS1","BUZZER",jst_xh,(2,),12.0,18.0,0,{"1":"+3V3","2":"BUZZER_DRV"})
add("Q4","N-FET SOT23",sot23,(3,0.95,2.6,1.0,0.6),20.0,18.0,0,
    {"1":"BUZZER","2":"GND","3":"BUZZER_DRV"},"buzzer surucu")
add("D2","SS14",chip,("0805",),20.0,14.5,0,{"1":"BUZZER_DRV","2":"+3V3"},"flyback")
add("R14","10k",chip,("0603",),24.0,18.0,0,{"1":"BUZZER","2":"GND"},"host yokken sessiz")
add("J10","QWIIC",jst_sh,(4,),58.0,46.0,0,{"1":"GND","2":"+3V3","3":"I2C_SDA","4":"I2C_SCL","MP1":"GND","MP2":"GND"})
add("J12","ESTOP BUTON",jst_xh,(2,),16.0,22.0,0,{"1":"ESTOP_BTN","2":"GND"})
add("J13","BUMPER",jst_xh,(3,),62.0,18.0,0,{"1":"GND","2":"BUMP1","3":"BUMP2"})
add("R10","4k7",chip,("0603",),52.0,24.0,0,{"1":"I2C_SDA","2":"+3V3"})
add("R11","4k7",chip,("0603",),52.0,22.0,0,{"1":"I2C_SCL","2":"+3V3"})

for i,(hx,hy) in enumerate(HOLES,1):
    add(f"MH{i}","M2.5",mount,(),hx,hy,0,{},"montaj")

# =============================================================================
# KAT PLANI  (85 x 56, kesit x42-60 / y0-14)
#   sol-ust   : USB-C, anten, durum LEDleri
#   sol-orta  : ESP32-S3
#   sol-alt   : guc zinciri (batarya -> koruma -> shunt -> estop -> BEC)
#   orta      : servo header x2 + PCA9685
#   sag-ust   : enkoder girisleri + tampon + Qwiic
#   sag-orta  : motor suruculer
#   sag-alt   : motor klemensleri
#   ust kenar : 40-pin disi soket (konumu Gemstone tarafindan dayatilir)
# =============================================================================
POS = {
 "J1":(J1_PIN1[0],J1_PIN1[1],0,"pin1"),
 # sol ust
 "J11":(3.0,44.0,90),"MH3":(3.5,52.5,0),"D1":(9.0,47.0,0),"R1":(9.0,45.2,0),"R2":(9.0,43.6,0),
 "J9":(3.0,32.0,0),
 "DS1":(3.8,25.5,0),"DS2":(3.8,20.5,0),"DS3":(3.8,15.5,0),"DS4":(3.8,10.5,0),
 # ESP32
 "U1":(17.0,32.0,0),"C3":(29.0,26.0,0),"C4":(29.0,24.0,0),
 "SW1":(32.0,40.0,0),"SW2":(32.0,35.0,0),"R3":(33.0,23.0,0),"R4":(36.5,23.0,0),
 "U6":(34.0,44.0,0),"C1":(31.0,47.0,90),"C2":(33.5,47.0,90),
 # guc zinciri
 "J2":(11.0,5.0,180),"MH1":(3.5,3.5,0),"F1":(22.0,5.0,0),"Q1":(29.0,5.0,180),"R5":(29.0,9.0,0),
 "RS1":(36.5,5.0,0),"U5":(36.5,9.0,0),"C5":(31.3,9.0,0),
 "J3":(11.0,10.0,0),"C7":(20.0,19.5,0),"J12":(22.0,10.5,0),
 "Q2":(66.0,20.0,180),"Q3":(66.0,11.5,0),"R6":(71.0,15.0,0),
 "U7":(22.0,14.0,0),"C13":(26.5,15.5,0),"R12":(26.5,12.5,0),"R13":(26.5,10.5,0),
 "L1":(22.0,17.5,0),"C6":(26.0,17.5,0),
 "LS1":(11.0,14.0,0),"Q4":(11.0,17.5,0),"D2":(15.0,17.5,0),"R14":(15.0,19.5,0),
 # servo + PCA
 "J8A":(48.0,45.0,0),"J8B":(48.0,36.0,0),"U4":(48.0,26.0,0),
 "C12":(55.5,29.0,0),"R9":(55.5,27.0,0),"R10":(55.5,24.0,0),"R11":(55.5,22.0,0),
 "J13":(79.0,47.0,0),
 # sag ust
 "MH4":(61.5,52.5,0),"J6":(69.0,53.0,0),"J7":(79.0,53.0,0),
 "U8":(70.0,46.0,0),"C11":(77.5,43.0,0),"J10":(78.5,40.0,0),
 # motor
 "U2":(70.0,35.0,0),"U3":(70.0,27.0,0),"C8":(78.0,31.0,0),
 "C9":(75.0,35.0,0),"C10":(75.0,27.0,0),"R7":(64.0,35.0,0),"R8":(64.0,27.0,0),
 "J4":(78.0,20.0,0),"J5":(78.0,8.0,0),"MH2":(61.5,3.5,0),
}
for _c in C:
    if _c["ref"] in POS:
        _p = POS[_c["ref"]]
        _c["x"], _c["y"], _c["rot"] = _p[0], _p[1], _p[2]
        _c["anchor"] = _p[3] if len(_p) > 3 else "center"
    else:
        _c["anchor"] = "center"
        print(f"UYARI: {_c['ref']} icin konum tanimlanmamis", file=__import__('sys').stderr)
