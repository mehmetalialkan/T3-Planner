# T3-Redstone — Bağlantı Listesi (netlist)

Şema yakalarken bu tabloyu kullan. `kicad/rs_design.py` bu listenin kaynağıdır.

Toplam **84 net**, **69 komponent**.

| Net | Bağlı uçlar |
|---|---|
| `GND` | C1.2, C10.2, C11.2, C12.2, C2.2, C3.2, C4.2, C5.2, C6.2, C7.2, C8.2, C9.2, J1.14, J1.20, J1.25, J1.30, J1.34, J1.39, J1.6, J1.9, J10.1, J10.MP1, J10.MP2, J11.A1, J11.A12, J11.B1, J11.B12, J11.S1, J11.S2, J12.2, J13.1, J2.2, J3.2, J6.2, J7.2, J8A.12, J8A.15, J8A.18, J8A.21, J8A.24, J8A.3, J8A.6, J8A.9, J8B.12, J8B.15, J8B.18, J8B.21, J8B.24, J8B.3, J8B.6, J8B.9, J9.2, Q3.2, Q4.2, R1.2, R13.2, R14.2, R2.2, R5.2, R7.2, R8.2, R9.2, SW1.3, SW1.4, SW2.3, SW2.4, U1.1, U1.40, U1.41, U2.10, U2.11, U2.6, U2.8, U2.EP, U3.10, U3.11, U3.6, U3.8, U3.EP, U4.1, U4.14, U4.2, U4.25, U4.3, U4.4, U4.5, U4.6, U5.4, U5.8, U6.2, U7.1, U8.10, U8.19, U8.6, U8.7, U8.8, U8.9 |
| `VBAT_RAW` | F1.1, J2.1 |
| `VBAT_F` | F1.2, Q1.5, Q1.6, Q1.7, Q1.8 |
| `VBAT` | Q1.1, Q1.2, Q1.3, RS1.1, U5.1 |
| `VSYS` | C7.1, J3.1, Q2.5, Q2.6, Q2.7, Q2.8, R6.2, RS1.2, U5.2, U5.9, U7.3, U7.5 |
| `VBAT_SW` | C10.1, C8.1, C9.1, Q2.1, Q2.2, Q2.3, U2.14, U2.15, U3.14, U3.15 |
| `+5V` | C1.1, C6.1, D1.2, J6.1, J7.1, J8A.11, J8A.14, J8A.17, J8A.2, J8A.20, J8A.23, J8A.5, J8A.8, J8B.11, J8B.14, J8B.17, J8B.2, J8B.20, J8B.23, J8B.5, J8B.8, L1.2, R12.1, U6.1, U6.3 |
| `+3V3` | C11.1, C12.1, C2.1, C3.1, C4.1, C5.1, D2.2, J10.2, LS1.1, R10.2, R11.2, R3.2, R4.2, U1.2, U2.7, U3.7, U4.28, U5.10, U5.7, U6.5, U8.1, U8.20 |
| `+5V_FB` | R12.2, R13.1, U7.4 |
| `+5V_USB` | D1.1, J11.A4, J11.A9, J11.B4, J11.B9 |
| `ANT` | J9.1 |
| `BOOT5V` | C13.1, U7.6 |
| `BOOT_BTN` | SW1.1, SW1.2, U1.27 |
| `BOOT_STRAP` | U1.15 |
| `BUMP1` | J13.2, U1.30 |
| `BUMP2` | J13.3, U1.29 |
| `BUZZER` | J1.37, Q4.1, R14.1 |
| `BUZZER_DRV` | D2.1, LS1.2, Q4.3 |
| `CC1` | J11.A5, R1.1 |
| `CC2` | J11.B5, R2.1 |
| `DBG_RX` | U1.36 |
| `DBG_TX` | U1.37 |
| `DRV_nFAULT` | R4.1, U1.9, U2.5, U3.5 |
| `DRV_nSLEEP` | U1.8, U2.2, U3.2 |
| `EN` | R3.1, SW2.1, SW2.2, U1.3 |
| `ENC_A1` | U1.12, U8.18 |
| `ENC_A1_5V` | J6.3, U8.2 |
| `ENC_A2` | U1.11, U8.16 |
| `ENC_A2_5V` | J7.3, U8.4 |
| `ENC_B1` | U1.10, U8.17 |
| `ENC_B1_5V` | J6.4, U8.3 |
| `ENC_B2` | U1.17, U8.15 |
| `ENC_B2_5V` | J7.4, U8.5 |
| `ESTOP_BTN` | J12.1, U1.32 |
| `ESTOP_DRV` | Q3.1, U1.23 |
| `ESTOP_GATE` | Q2.4, Q3.3, R6.1 |
| `ESTOP_STAT` | J1.13, U1.20 |
| `GND_GATE` | Q1.4, R5.1 |
| `GPIO10` | U1.18 |
| `GPIO11` | U1.19 |
| `HOST_RX` | J1.10, U1.25 |
| `HOST_TX` | J1.8, U1.24 |
| `I2C_SCL` | J10.4, R11.1, U1.35, U4.26, U5.5 |
| `I2C_SDA` | J10.3, R10.1, U1.34, U4.27, U5.6 |
| `IPROPI_A` | R7.1, U1.39, U2.1 |
| `IPROPI_B` | R8.1, U1.38, U3.1 |
| `LED_D1` | DS1.2, DS2.1 |
| `LED_D2` | DS2.2, DS3.1 |
| `LED_D3` | DS3.2, DS4.1 |
| `LED_D4` | DS4.2 |
| `LED_DATA` | DS1.1, U1.31 |
| `MA_EN` | U1.5, U2.3 |
| `MA_PH` | U1.4, U2.4 |
| `MB_EN` | U1.7, U3.3 |
| `MB_PH` | U1.6, U3.4 |
| `OE_N` | R9.1, U4.24 |
| `OUTA1` | J4.1, U2.13, U2.16 |
| `OUTA2` | J4.2, U2.12, U2.9 |
| `OUTB1` | J5.1, U3.13, U3.16 |
| `OUTB2` | J5.2, U3.12, U3.9 |
| `PWR_ALERT` | U5.3 |
| `SERVO1` | J8A.1, U4.7 |
| `SERVO10` | J8B.4, U4.17 |
| `SERVO11` | J8B.7, U4.18 |
| `SERVO12` | J8B.10, U4.19 |
| `SERVO13` | J8B.13, U4.20 |
| `SERVO14` | J8B.16, U4.21 |
| `SERVO15` | J8B.19, U4.22 |
| `SERVO16` | J8B.22, U4.23 |
| `SERVO2` | J8A.4, U4.8 |
| `SERVO3` | J8A.7, U4.9 |
| `SERVO4` | J8A.10, U4.10 |
| `SERVO5` | J8A.13, U4.11 |
| `SERVO6` | J8A.16, U4.12 |
| `SERVO7` | J8A.19, U4.13 |
| `SERVO8` | J8A.22, U4.15 |
| `SERVO9` | J8B.1, U4.16 |
| `SPARE2` | U1.21 |
| `SPARE3` | U1.22 |
| `SPARE4` | U1.33 |
| `SPARE5` | U1.28 |
| `SW5V` | C13.2, L1.1, U7.2 |
| `USB_DM` | J11.A7, J11.B7, U1.13 |
| `USB_DP` | J11.A6, J11.B6, U1.14 |

## Doğrulanması gereken pinoutlar

Aşağıdaki entegrelerin pin atamaları veri sayfasından **tek tek doğrulanmalı** —
bu tasarımda hafızadan yazıldılar ve üretime gitmeden önce kontrol şart:

| Parça | Risk |
|---|---|
| ESP32-S3-WROOM-1U | 41 pad'in numaralandırması ve footprint ölçüleri |
| DRV8874 (HTSSOP-16) | VREF/PMODE/GND pin sırası |
| PCA9685 (TSSOP-28) | LED0-15 dağılımı, A0-A5 konumu |
| INA226 (VSSOP-10) | IN+/IN-/VBUS sırası |
| TPS563201 (SOT-23-6) | 1=GND 2=SW 3=VIN 4=FB 5=EN 6=VBST |
| AP2112K (SOT-23-5) | 1=VIN 2=GND 3=EN 4=NC 5=VOUT |
| SOT-23 pin düzeni | sol/sağ sıra yönü ters olabilir |
