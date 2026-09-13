# T3 Gemstone O1 — Donanım Analizi

Kaynaklar: `t3gemstone/docs` (tüm `tr/boards/o1/**` ve `tr/projects/**`),
`t3gemstone/hardware` (blok diyagram, v0.2 layout PDF, Fritzing PCB).
`t3gemstone.org` ve `docs.t3gemstone.org` bu oturumda ağ politikası nedeniyle
erişilemedi; her şey GitHub üzerinden okundu.

## 1. Mekanik — Raspberry Pi Model B form faktörü

Fritzing PCB dosyasından (72 birim/inch) ölçüldü:

| Ölçü | Değer |
|---|---|
| Kart | **85.00 × 56.00 mm** |
| Köşe yarıçapı | 3.00 mm |
| Montaj deliği aralığı | **58.0 × 49.0 mm** |
| Sol kenardan ilk delik | 3.50 mm |
| Delik konumları | (3.5, 3.5) (61.5, 3.5) (3.5, 52.5) (61.5, 52.5) |

Raspberry Pi Model B ile birebir aynı. **Sonuç: hazır Raspberry Pi HAT
şablonları doğrudan kullanılabilir.**

Layout PDF'inde `MH1..MH7` yani **7 montaj deliği** görünüyor; Fritzing dosyası
yalnızca 4'ünü çiziyor. Kalan 3'ünün konumu kumpasla doğrulanmalı.

## 2. 40-pin header — Raspberry Pi ile %100 uyumlu

Fiziksel pin numaralandırması BCM ile birebir aynı:

| Pin | Sinyal | Pin | Sinyal |
|----:|---|----:|---|
| 1 | 3V3 | 2 | 5V |
| 3 | GPIO-2 · I2C-MCU0 SDA | 4 | 5V |
| 5 | GPIO-3 · I2C-MCU0 SCL | 6 | GND |
| 7 | GPIO-4 | 8 | GPIO-14 · UART-MAIN1 TX |
| 9 | GND | 10 | GPIO-15 · UART-MAIN1 RX |
| 11 | GPIO-17 | 12 | GPIO-18 · McASP0 CLK |
| 13 | GPIO-27 | 14 | GND |
| 15 | GPIO-22 | 16 | GPIO-23 |
| 17 | 3V3 | 18 | GPIO-24 |
| 19 | GPIO-10 · SPI-MCU0 MOSI | 20 | GND |
| 21 | GPIO-9 · SPI-MCU0 MISO | 22 | GPIO-25 |
| 23 | GPIO-11 · SPI-MCU0 SCLK | 24 | GPIO-8 · SPI-MCU0 CS0 |
| 25 | GND | 26 | GPIO-7 · SPI-MCU0 CS2 |
| 27 | GPIO-0 · I2C-WKUP0 SDA | 28 | GPIO-1 · I2C-WKUP0 SCL |
| 29 | GPIO-5 | 30 | GND |
| 31 | GPIO-6 | 32 | GPIO-12 · PWM-ECAP0 |
| 33 | GPIO-13 · PWM-1B | 34 | GND |
| 35 | GPIO-19 | 36 | GPIO-16 |
| 37 | GPIO-26 | 38 | GPIO-20 · McASP0 DIN |
| 39 | GND | 40 | GPIO-21 · McASP0 DOUT |

> Doküman hatası: T3'ün `37-i2c.png` görselinde pin 35 "I2C-WKUP0 SDA" diye
> etiketlenmiş. Yanlış — o etiket pin 27'ye ait. GPIO-19'un muxleri
> SPI2_CS3 / GPIO1_12 / EQEP1_B.

### 2.1. Toplam I/O bütçesi
**28 GPIO + 2×3V3 + 2×5V + 8×GND.** Başka fiziksel genişleme yok.
Fan, CAN, JTAG, UART konsol ve RTC pil konnektörleri ayrı durur, HAT'ten erişilmez.

## 3. Kartta ZATEN olan çevre birimler

| Birim | Parça | Arayüz |
|---|---|---|
| SoC | TI AM67A — 4× A53 @1.4 GHz, **2× R5F @800 MHz**, 2× C7x DSP (4 TOPS), BXS-4-64 GPU | — |
| RAM / Flash | 4 GB LPDDR4 · 32 GB eMMC · AT24C512 EEPROM | — |
| Depolama | microSD (SDR104) · **M.2 2280 NVMe (arka yüz)** | — |
| **IMU** | **InvenSense ICM-20948** 9 eksen (AK09916 manyetometre dahil) | SPI `/dev/spidev0.3` |
| **Barometre** | ST LPS22DF 24-bit | SPI |
| Nem/sıcaklık | TI HDC2010 | I2C |
| **RTC** | Maxim DS1340 + 2-pin JST SH pil konnektörü | I2C |
| **CAN FD** | TI TCAN1462-Q1 → **J26** (GND/L/H) | Ayrı konnektör |
| Kablosuz | Fn-Link 6222B-SRC — **Wi-Fi 5 (802.11ac) + BT 5.0** | SDIO / UART |
| Ethernet | Gigabit RJ45 | RGMII |
| USB | 2× USB3.0-A · 1× USB2.0-A · 1× USB-C · 1× USB-C (device + PD) | USB3 HUB + MUX |
| Video | 2× 4-lane MIPI CSI · 1× MIPI DSI · HDMI | FPC 22 pin |
| Fan | 4-pin JST SH, **PWM + TACH** | PWM-2A |
| Debug | JTAG (Plug-of-Nails) · 3-pin UART konsol (J21) | — |
| Boot | SW2/SW3 — 8'li DIP ×2, BOOT MODE 0–15 | — |

**Şu blokları shield'e koymak tekrardır:** IMU, barometre, RTC, CAN
transceiver, Wi-Fi/BT, nem-sıcaklık, fan sürücü, AI hızlandırıcı.

## 4. Güç mimarisi — ve bir uyuşmazlık

Blok diyagramına göre:

```
Type-C Power ──5-9V──> E-FUSE 1 ──┐
                                   ├──> Main DC-DC Buck x2 ──> 5V ──> PMIC
DC Power Connector ──5-9V──> E-FUSE 2 ──┘                              │
                                          0.8 / 1.1 / 1.2 / 1.8 / 2.5 / 3.3 V
```

| Kaynak | DC giriş aralığı |
|---|---|
| Kart özellikleri sayfası (`introduction.mdx`) | **5–12 V / 5 A** |
| Blok diyagramı (`t3-gem-o1-block-diagram.png`) | **5–9 V** |

**Bu çelişki çözülmeden 3S LiPo (9.0–12.6 V) bağlanmamalı.** Her iki okumada da
güvenli olan tek seçenek **2S LiPo (6.0–8.4 V)**. Redstone bu yüzden 2S üzerine
kurgulanıyor. Girişlerin önünde e-fuse var (layout'ta `F1`), yani aşırı gerilimde
muhtemelen kesip kartı koruyacaktır — ama buna güvenerek tasarım yapılmaz.

Giriş konnektörleri: **yeşil 2 kutuplu klemens** (+/−, "Harici Güç") ve
**USB-C (Güç ve Konsol)**. RTC'nin ayrı 3 V pil girişi vardır.

## 5. PWM — 7 kanal ve gizli bir tuzak

| Arayüz | Cihaz | GPIO |
|---|---|---|
| PWM-ECAP0 | `pwmchip0/pwm0` | GPIO-12 |
| PWM-ECAP1 | `pwmchip1/pwm0` | GPIO-16 |
| PWM-ECAP2 | `pwmchip2/pwm0` | GPIO-18 |
| PWM-0A | `pwmchip3/pwm0` | GPIO-5 |
| PWM-0B | `pwmchip3/pwm1` | GPIO-14 |
| PWM-1A | `pwmchip5/pwm0` | GPIO-6 |
| PWM-1B | `pwmchip5/pwm1` | GPIO-13 |
| PWM-2A | `pwmchip7/pwm0` | FAN header |

> **TUZAK:** Aynı çipin iki kanalına farklı periyot ATANAMAZ.
> `pwmchip3` (GPIO-5 + GPIO-14) ve `pwmchip5` (GPIO-6 + GPIO-13) çiftleri
> periyot paylaşır. 50 Hz servo + 400 Hz ESC aynı çipe düşerse çalışmaz.
> Gerçekte **3 bağımsız periyotlu (ECAP) + 2 bağlı çift** kanal vardır.

## 6. Donanım enkoder sayıcı (EQEP) HAT'e çıkmış

Pinmux tablosundan çıkarıldı — dokümanlarda hiç vurgulanmamış:

| EQEP | A | B | I | S |
|---|---|---|---|---|
| EQEP0 | GPIO-16 | GPIO-17 | GPIO-20 | GPIO-21 |
| EQEP1 | GPIO-18 | GPIO-19 | GPIO-14 | GPIO-15 |
| EQEP2 | — | — | GPIO-4 | — |

**EQEP0 ve EQEP1 kullanılabilir** (EQEP2'nin A/B'si header'da yok). Yani host
iki tekerleğin enkoderini donanımda sayabilir. Hazır overlay yok, yazılması gerekir.

## 7. R5F gerçek zamanlı çekirdekler — sıfır toplamlı

R5F'ler ayrı bir mikrodenetleyici değil, AM67A'nın içinde. **Kendi pinleri yok**;
aynı pinleri Linux'tan device-tree ile koparman gerekir
(`tr/boards/o1/peripherals/mcu.mdx` §3). Yani R5F ekstra I/O getirmez.

Araç zinciri ağır: TI Processor SDK RTOS J722S, SysConfig, CGT C7000, ARM LLVM,
remoteproc, `/lib/firmware`. Yarışma takımları için giriş bariyeri yüksek.

## 8. ArduPilot — T3'ün kendi saydığı eksikler

`tr/projects/ardupilot.mdx` şunları **harici** olarak işaretliyor:

| Eksik | Doküman ifadesi |
|---|---|
| Batarya izleme (ADS1115 @0x48, I2C-MCU0) | "harici olarak bağlanabilir" — **kartta hiç ADC yok** |
| Buzzer (GPIO-26) | "harici olarak bağlanabilir" |
| SBUS sinyal tersleyici (NPN + 10k + 1k) | "**kullanmanız gerekir**" — zorunlu |
| GPS (UART-MAIN6) + harici pusula (I2C-MCU0) | harici modül |
| Telemetri radyosu (UART-WKUP0) | harici modül |

**UART-MAIN6 aktif edilince Bluetooth devre dışı kalır.**

## 9. Kartın gerçek eksik listesi

| Eksik | Etki |
|---|---|
| **ADC yok** | Analog sensör, batarya, potansiyometre imkânsız |
| PWM kıtlığı (7, çifti bağlı) | Çok eksenli araç zor |
| Motor güç katı yok | Her robot projesinde harici sürücü |
| Geniş gerilim girişi yok | LiPo doğrudan bağlanamaz (2S hariç) |
| Brownout/hold-up yok | Motor stall → reset → eMMC bozulması |
| Ters polarite koruması belirsiz | Takımlar bataryayı ters takar |
| Bağımsız güvenlik alanı yok | Acil stop, koruduğu bilgisayara bağımlı |
| Enkoder için 5 V tampon yok | EQEP var ama 5 V enkoder bağlanamaz |
