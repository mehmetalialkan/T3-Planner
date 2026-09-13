# T3-Redstone

**T3 Gemstone O1 için ROS 2 mobil robot kontrol kartı.**
Gazebo ile aynı yazılımı çalıştıran, TurtleBot sınıfı bir platform.

## Neden

Gemstone O1 güçlü bir bilgisayar ama robot yapmak için üç şeyi yok:

| Eksik | Sonuç |
|---|---|
| **Hiç ADC yok** | Analog sensör, batarya izleme, potansiyometre imkânsız |
| **Motor güç katı yok** | Her takım kendi sürücüsünü breadboard'da kuruyor |
| **7 PWM, ikisi periyot-bağlı** | 50 Hz servo + 400 Hz ESC aynı çipte çalışmıyor |

Redstone bunları ekler ve motor/enkoder işini ESP32-S3'e devrederek Linux'u
gerçek zamanlı kontrol yükünden kurtarır.

## Mimari

```
Gemstone O1 (Linux, ROS 2)              Redstone (ESP32-S3)
├── Nav2 / slam_toolbox                 ├── Tekerlek PID hiz kontrolu
├── ros2_control                        ├── Enkoder sayimi (PCNT, donanim)
│   └── RedstoneHardware ──UART──────>  ├── 16 kanal servo (PCA9685)
├── IMU: ICM-20948 (kartta zaten var)   ├── Batarya izleme (INA226)
└── LiDAR: RPLIDAR USB                  └── Acil stop + watchdog
```

**Kartta zaten olanı tekrar etmiyoruz:** IMU, barometre, RTC, CAN, Wi-Fi/BT,
fan sürücü — hepsi Gemstone'un üstünde.

## Gazebo uyumluluğu

Tek `use_sim` argümanıyla geçiş. Üstteki hiçbir katman değişmez:

```
use_sim:=false -> RedstoneHardware (SystemInterface) -> UART -> ESP32
use_sim:=true  -> gz_ros2_control/GazeboSimSystem    -> Gazebo
```

Aynı URDF, aynı `controllers.yaml`, aynı launch:
`diff_drive_controller` (`/cmd_vel` → `/odom` + TF), `joint_state_broadcaster`.

## Mekanik

Gemstone O1'in kendi Fritzing dosyasından ölçüldü — **Raspberry Pi Model B
form faktörü**:

| | Gemstone O1 | Redstone |
|---|---|---|
| Boyut | 85.0 × 56.0 mm | **85.0 × 56.0 mm** (tam boy) |
| Köşe | 3.0 mm | 3.0 mm |
| Delikler | 58 × 49 mm, sol kenardan 3.5 mm | aynı |
| Header | 2×20 erkek | **2×20 dişi soket, yüksek** |

### Kamera / DSI kesiti
Alt kenara açık bir U kesit: FPC kablosu dışarı çıkar, mandala parmak girer,
frezelemesi kolaydır. Varsayılan `X 42→60 mm, derinlik 14 mm`.
**Bu değerler fotoğraftan tahmin edildi — J4 (CSI) ve J12 (CSI/DSI)
konnektörlerini kumpasla ölç**, `kicad/gen_kicad.py` içindeki `CUT_*`
sabitlerini güncelle ve betiği tekrar çalıştır.

### Yüksek header zorunlu
Tam boy shield, Gemstone'un **USB-A yığını ve RJ45'inin üzerinden geçer**
(~13.5 mm). Bu yüzden 2×20 dişi soket **en az 16 mm geçiş yüksekliğinde**
olmalı ve standoff'lar da aynı boyda seçilmeli. Shield'in ALT yüzeyine
komponent konulmaz.

## Güç — 2S LiPo, kartta buck yok

Gemstone'un DC girişi zaten regülatörlü, ham batarya gerilimini yiyor.
Redstone sadece **sigorta + ters polarite koruması + acil stop ayrımı + servo BEC**
yapar. Ayrıntı: [docs/03-guc-mimarisi.md](docs/03-guc-mimarisi.md)

> ⚠ Gemstone'un DC giriş aralığı iki kaynakta farklı yazıyor (5–12 V vs 5–9 V).
> Çözülene kadar **yalnızca 2S (6.0–8.4 V)** — her iki okumada da güvenli.

## Dosyalar

| Yol | İçerik | Durum |
|---|---|---|
| `kicad/t3-redstone.kicad_pcb` | **Yerleşimi yapılmış KiCad 8 board** — 69 komponent, 84 net, 4 katman, kırmızı maske, ENIG, güç düzlemleri, güç yolları, ipek baskı | **Hazır — KiCad'de aç** |
| `kicad/rs_lib.py` · `rs_design.py` · `rs_emit.py` · `rs_render.py` | Board üreteci: footprint kütüphanesi, devre+kat planı, emitter, DRC+önizleme. Bir koordinatı değiştir, `python3 rs_emit.py` çalıştır | Hazır |
| `mekanik/t3-redstone-preview.svg` | Kartın görsel önizlemesi | Hazır |
| `docs/04-netlist.md` | 84 netin tam bağlantı listesi + doğrulanacak pinoutlar | Hazır |
| `mekanik/t3-redstone-outline.dxf` | Kontur + delikler (her CAD'e girer) | Hazır |
| `docs/01-gemstone-o1-analiz.md` | Gemstone O1 tam donanım analizi, 40-pin tablosu, EQEP, PWM tuzağı | Hazır |
| `docs/02-pin-plani.md` | Host + ESP32 pin atamaları, I2C adres haritası | Hazır |
| `docs/03-guc-mimarisi.md` | Güç topolojisi ve kuralları | Hazır |
| `bom/bom.csv` | Parça listesi, MPN'li | Taslak |
| Şema (`.kicad_sch`) | — | **Yapılacak** — `docs/04-netlist.md`'den yakala |
| Sinyal routing | — | **Yapılacak** — güç ve GND bitti, sinyaller elde |

## Kartın durumu

**Bitmiş olanlar**
- 69 komponent yerleştirildi, çakışma kontrolünden temiz geçti
- 4 katman: `F.Cu` sinyal · `In1.Cu` tam GND düzlemi · `In2.Cu` bölünmüş güç düzlemi · `B.Cu` sinyal + GND
- `In2.Cu` güç düzlemleri çakışmasız bölündü: VSYS / +3V3 / +5V / VBAT_SW
- Güç zinciri yolları çizildi ve kendi DRC'mden temiz geçti
- Yüksek akımlı düğümler (Q1, Q2 çevresi) yol yerine yerel bakır alanla çözüldü
- 33 GND dikiş viası
- İpek baskı: blok etiketleri, uyarılar, pin 1 işareti
- **Kırmızı lehim maskesi + ENIG** stackup'ta tanımlı

**Kalan iş**
- Şema yakalama (netlist hazır)
- Sinyal yollarının çizimi (güç bitti)
- KiCad'in kendi DRC'si — benim kontrolüm yol/pad ve yerleşim çakışmasına bakıyor,
  KiCad'inki üretim kurallarına da bakar

## Güç topolojisi

```
XT60 -> F1 sigorta -> Q1 ters polarite -> RS1 shunt -> VSYS
                                                        |
                        +-------------------------------+
                        |            |                  |
                    J3 klemens    U7 5V BEC        Q2 ACIL STOP
                    (Gemstone)    (servo rayi)          |
                                                    VBAT_SW -> DRV8874 x2
```

Q2 arızada **kapalıdır**: gate VSYS'e pull-up'lı, açmak için ESP32'nin
Q3'ü sürmesi gerekir. ESP32 ölürse motorlar durur.

## Çizim sırası

1. Güç zinciri (XT60 → sigorta → ters polarite → passthrough + kollar)
2. ESP32-S3 + USB-C + otomatik reset + BOOT/RESET
3. DRV8874 ×2 + enkoder tamponu + klemensler
4. PCA9685 + servo header + 5 V BEC
5. I2C zinciri (INA226, OLED, Qwiic)
6. 40-pin header + acil stop + WS2812

4 katman: Sig / GND / PWR / Sig. Motor-servo güç bölgesi ile mantık bölgesini
ayır, tek noktadan GND birleştir.

## Doğrulanacaklar

1. **Gemstone DC giriş aralığı** — 5–9 V mı 5–12 V mi? (T3'e sor / e-fuse MPN'ine bak)
2. **40-pin header konumu** — el yapımı Fritzing parçasından ölçüldü, kumpasla teyit et
3. **Montaj delikleri** — layout PDF'inde MH1..MH7 var, Fritzing sadece 4'ünü çiziyor
4. **Stacking header yüksekliği** — Gemstone'un üst yüzeyindeki en yüksek eleman ölçülmeli
