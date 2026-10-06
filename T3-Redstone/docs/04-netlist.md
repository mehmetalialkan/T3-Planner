# T3-Redstone — Bağlantı Listesi (netlist)

> Bu dosya `kicad/rs_docs.py` ile `kicad/rs_design.py`'den **üretilir** — elle düzenleme.
> Şema (`kicad/t3-redstone.kicad_sch`) ve kart aynı kaynaktan gelir; `rs_sch.py --check`
> şemadan çıkan netlisti bu tabloyla pin pin karşılaştırır.

Toplam **83 net**, **83 komponent** (+4 montaj deliği).

| Net | Bağlı uçlar |
|---|---|
| `+3V3` | C2.1, C3.1, C4.1, C5.1, C11.1, C12.1, J10.2, J14.1, R3.2, R4.2, R10.2, R11.2, R15.2, R17.2, U1.2, U2.5, U3.5, U4.28, U5.1, U5.2, U5.6, U6.5, U8.1, U8.20 |
| `+5V` | C1.1, C6.1, C15.1, C17.1, C18.1, C19.1, C20.1, C21.1, D1.1, D2.1, DS1.4, DS2.4, DS3.4, DS4.4, J6.1, J7.1, J8A.2, J8A.5, J8A.8, J8A.11, J8A.14, J8A.17, J8A.20, J8A.23, J8B.2, J8B.5, J8B.8, J8B.11, J8B.14, J8B.17, J8B.20, J8B.23, L1.2, LS1.1, R12.1, RN1.5, RN1.6, RN1.7, RN1.8, U6.1, U6.3, U9.5 |
| `GND` | C1.2, C2.2, C3.2, C4.2, C5.2, C6.2, C7.2, C8.2, C9.2, C10.2, C11.2, C12.2, C14.2, C15.2, C16.2, C17.2, C18.2, C19.2, C20.2, C21.2, DS1.2, DS2.2, DS3.2, DS4.2, J1.6, J1.9, J1.14, J1.20, J1.25, J1.30, J1.34, J1.39, J2.2, J3.2, J6.2, J7.2, J8A.3, J8A.6, J8A.9, J8A.12, J8A.15, J8A.18, J8A.21, J8A.24, J8B.3, J8B.6, J8B.9, J8B.12, J8B.15, J8B.18, J8B.21, J8B.24, J10.1, J10.MP, J11.A1, J11.A12, J11.B1, J11.B12, J11.S1, J12.2, J13.1, J14.4, Q4.2, R1.2, R2.2, R5.2, R7.2, R8.2, R9.2, R13.2, R14.2, R16.2, SW1.2, SW2.2, U1.1, U1.40, U1.41, U2.7, U2.9, U2.15, U2.16, U2.17, U3.7, U3.9, U3.15, U3.16, U3.17, U4.1, U4.2, U4.3, U4.4, U4.5, U4.14, U4.24, U4.25, U5.7, U6.2, U7.1, U8.6, U8.7, U8.8, U8.9, U8.10, U8.19, U9.1, U9.3, U10.2 |
| `VBAT` | Q1.1, Q1.2, Q1.3, RS1.1, U5.10 |
| `VBAT_F` | F1.2, Q1.5, Q1.6, Q1.7, Q1.8 |
| `VBAT_RAW` | F1.1, J2.1 |
| `VBAT_SW` | C8.1, C9.1, C10.1, C22.2, C23.2, Q2.5, Q2.6, Q2.7, Q2.8, U2.11, U3.11 |
| `VSYS` | C7.1, C16.1, J3.1, Q2.1, Q2.2, Q2.3, R6.2, RS1.2, U5.8, U5.9, U7.3, U7.5 |
| `+5V_FB` | R12.2, R13.1, U7.4 |
| `+5V_USB` | D1.2, J11.A4, J11.A9, J11.B4, J11.B9, U10.5 |
| `BOOT5V` | C13.1, U7.6 |
| `BOOT_BTN` | SW1.1, U1.27 |
| `BUMP1` | J13.2, U1.31 |
| `BUMP2` | J13.3, U1.32 |
| `BUZZER` | J1.37, Q4.1, R14.1 |
| `BUZZER_DRV` | D2.2, LS1.2, Q4.3 |
| `CC1` | J11.A5, R1.1 |
| `CC2` | J11.B5, R2.1 |
| `CPH_A` | C24.1, U2.13 |
| `CPH_B` | C25.1, U3.13 |
| `CPL_A` | C24.2, U2.14 |
| `CPL_B` | C25.2, U3.14 |
| `DRV_nFAULT` | R4.1, U1.9, U2.4, U3.4 |
| `DRV_nSLEEP` | U1.8, U2.3, U3.3 |
| `EN` | C14.1, R3.1, SW2.1, U1.3 |
| `ENC_A1` | U1.12, U8.18 |
| `ENC_A1_5V` | J6.3, RN1.1, U8.2 |
| `ENC_A2` | U1.18, U8.16 |
| `ENC_A2_5V` | J7.3, RN1.3, U8.4 |
| `ENC_B1` | U1.17, U8.17 |
| `ENC_B1_5V` | J6.4, RN1.2, U8.3 |
| `ENC_B2` | U1.19, U8.15 |
| `ENC_B2_5V` | J7.4, RN1.4, U8.5 |
| `ESTOP_DRV` | Q3.1, R16.1, U1.23 |
| `ESTOP_GATE` | Q2.4, Q3.3, R6.1 |
| `ESTOP_LOOP` | J12.1, Q3.2, R17.1, U1.11 |
| `ESTOP_STAT` | J1.13, U1.20 |
| `GND_GATE` | Q1.4, R5.1 |
| `GPIO13` | J14.2, U1.21 |
| `GPIO17` | J14.3, U1.10 |
| `HOST_RX` | J1.10, U1.24 |
| `HOST_TX` | J1.8, U1.25 |
| `I2C_SCL` | J10.4, R11.1, U1.35, U4.26, U5.5 |
| `I2C_SDA` | J10.3, R10.1, U1.34, U4.27, U5.4 |
| `IPROPI_A` | R7.1, U1.39, U2.6 |
| `IPROPI_B` | R8.1, U1.38, U3.6 |
| `LED_D1` | DS1.1, DS2.3 |
| `LED_D2` | DS2.1, DS3.3 |
| `LED_D3` | DS3.1, DS4.3 |
| `LED_D4` | DS4.1 |
| `LED_DATA` | U1.33, U9.2 |
| `LED_DIN` | DS1.3, U9.4 |
| `MA_EN` | U1.5, U2.1 |
| `MA_PH` | U1.4, U2.2 |
| `MB_EN` | U1.7, U3.1 |
| `MB_PH` | U1.6, U3.2 |
| `OE_N` | R9.1, U4.23 |
| `OUTA1` | J4.1, U2.8 |
| `OUTA2` | J4.2, U2.10 |
| `OUTB1` | J5.1, U3.8 |
| `OUTB2` | J5.2, U3.10 |
| `PWR_ALERT` | R15.1, U1.22, U5.3 |
| `SERVO1` | J8A.1, U4.6 |
| `SERVO2` | J8A.4, U4.7 |
| `SERVO3` | J8A.7, U4.8 |
| `SERVO4` | J8A.10, U4.9 |
| `SERVO5` | J8A.13, U4.10 |
| `SERVO6` | J8A.16, U4.11 |
| `SERVO7` | J8A.19, U4.12 |
| `SERVO8` | J8A.22, U4.13 |
| `SERVO9` | J8B.1, U4.15 |
| `SERVO10` | J8B.4, U4.16 |
| `SERVO11` | J8B.7, U4.17 |
| `SERVO12` | J8B.10, U4.18 |
| `SERVO13` | J8B.13, U4.19 |
| `SERVO14` | J8B.16, U4.20 |
| `SERVO15` | J8B.19, U4.21 |
| `SERVO16` | J8B.22, U4.22 |
| `SW5V` | C13.2, L1.1, U7.2 |
| `USB_DM` | J11.A7, J11.B7, U1.13, U10.3, U10.4 |
| `USB_DP` | J11.A6, J11.B6, U1.14, U10.1, U10.6 |
| `VCP_A` | C22.1, U2.12 |
| `VCP_B` | C23.1, U3.12 |

## Pinout doğrulaması

| Parça | Kaynak | Durum |
|---|---|---|
| ESP32-S3-WROOM-1U | KiCad `RF_Module:ESP32-S3-WROOM-1` sembolü + resmi `ESP32-S3-WROOM-1U` footprint'i | ✔ |
| INA226 (VSSOP-10) | KiCad `Sensor_Energy:INA226` | ✔ |
| PCA9685PW (TSSOP-28) | KiCad `Driver_LED:PCA9685PW` | ✔ |
| TPS563201 (SOT-23-6) | KiCad `Regulator_Switching:TPS563200` (aynı pinout) | ✔ |
| AP2112K-3.3 (SOT-23-5) | KiCad `Regulator_Linear:AP2112K-3.3` | ✔ |
| SK6812MINI | KiCad `LED:SK6812MINI` — 1=DOUT 2=VSS 3=DIN 4=VDD | ✔ |
| 74LVC245 (TSSOP-20) | KiCad `74xx:74HC245` (aynı pinout) | ✔ |
| 74AHCT1G125 (SOT-23-5) | KiCad `74xGxx:74AHCT1G125` | ✔ |
| USBLC6-2SC6 | KiCad `Power_Protection:USBLC6-2SC6` | ✔ |
| AO4407A (SO-8) | KiCad `Transistor_FET:FDS9435A` ile aynı: 1-3 S, 4 G, 5-8 D | ✔ |
| AO3400A (SOT-23) | KiCad `Transistor_FET:AO3400A`: 1 G, 2 S, 3 D | ✔ |
| B5819W (SOD-123) | KiCad `Diode_SMD:D_SOD-123`: **pad 1 = katot** | ✔ |
| DRV8874 (HTSSOP-16) | KiCad'de yok. TI SLVSF66: 1 EN/IN1, 2 PH/IN2, 3 nSLEEP, 4 nFAULT, 5 VREF, 6 IPROPI, 7 IMODE, 8 OUT1, 9 PGND, 10 OUT2, 11 VM, 12 VCP, 13 CPH, 14 CPL, 15 GND, 16 PMODE | ⚠ siparişten önce veri sayfasıyla bir kez daha bak |
