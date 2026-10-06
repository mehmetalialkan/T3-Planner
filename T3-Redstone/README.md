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
frezelemesi kolaydır. Şu anki değer `X 40→57 mm, derinlik 14 mm`.
**Bu değerler fotoğraftan tahmin edildi — Gemstone'un J4 (CSI) ve J12 (CSI/DSI)
konnektörlerini kumpasla ölç**, `kicad/rs_design.py` içindeki `CUT` sözlüğünü
güncelle ve `make` ile kartı yeniden üret.

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

| Yol | İçerik |
|---|---|
| `kicad/t3-redstone.kicad_pcb` | **Kart** — 4 katman, kırmızı maske, ENIG, yerleşim + güç + sinyal yolları + GND dolgu |
| `kicad/t3-redstone.kicad_sch` | **Şema** — `rs_design.py`'den üretilir, netlist kartla pin pin aynı |
| `kicad/rs_design.py` | **Tek kaynak**: parçalar, footprint'ler, pad → net, yerleşim, güç dağıtımı |
| `kicad/rs_build.py` | Kartı KiCad'in `pcbnew` API'siyle kurar (resmi kütüphane footprint'leri) |
| `kicad/rs_route.py` | Freerouting ile sinyal yönlendirme, GND dikiş viaları, dolgu, KiCad DRC |
| `kicad/rs_sch.py` | Şemayı üretir; `--check` şemadan netlist çıkarıp tasarımla karşılaştırır |
| `kicad/rs_bom.py` · `rs_docs.py` · `rs_render.py` | BOM, netlist belgesi, önizleme SVG |
| `kicad/T3RS.pretty` · `T3RS.kicad_sym` | Projeye özel footprint (servo 3×8) ve semboller (DRV8874, servo) |
| `mekanik/t3-redstone-preview.svg` | Kartın üstten görünümü (kicad-cli) |
| `mekanik/t3-redstone-outline.dxf` | Kontur + delikler (her CAD'e girer) |
| `bom/bom.csv` | Parça listesi, MPN'li — `rs_design.py`'den üretilir |
| `docs/01-gemstone-o1-analiz.md` | Gemstone O1 donanım analizi, 40-pin tablosu, EQEP, PWM tuzağı |
| `docs/02-pin-plani.md` | Host + ESP32 pin atamaları, I2C adres haritası |
| `docs/03-guc-mimarisi.md` | Güç topolojisi, acil stop zinciri, katman dağılımı |
| `docs/04-netlist.md` | Bütün netlerin bağlantı listesi + pinout doğrulama tablosu (üretilir) |
| `docs/05-revB-degisiklikler.md` | **Rev A'da bulunan hatalar ve düzeltmeler** |

### Yeniden üretmek

```bash
cd kicad
make            # rs_build -> rs_route -> rs_sch --check -> BOM / netlist / önizleme
```

KiCad 7 (`pcbnew` Python modülüyle), Java 25+ ve Freerouting 2.4.1 gerekir
(`FREEROUTING_JAR=...`, Maven Central: `app.freerouting:freerouting:2.4.1`, `-executable.jar`).
Bir pin ya da koordinat değiştirmek için yalnızca `rs_design.py`'yi düzenle.
Dosyalar KiCad 7 biçiminde üretilir; KiCad 8 / 9 açar.

## Kartın durumu (rev B)

**Bitmiş olanlar**
- Bütün entegre pinleri resmi kütüphaneyle / veri sayfasıyla karşılaştırıldı; rev A'daki
  14 kritik hata düzeltildi — liste: [docs/05-revB-degisiklikler.md](docs/05-revB-degisiklikler.md)
- 87 komponent (resmi KiCad footprint'leri), 83 net; yerleşim çakışmasız
- 4 katman: `F.Cu` sinyal + güç dökümleri · `In1.Cu` kesintisiz GND · `In2.Cu` bölünmüş güç
  (VSYS / +5V / +3V3 / VBAT_SW) · `B.Cu` sinyal + GND dolgu
- **Bütün sinyal netleri yönlendirildi** (Freerouting + KiCad DRC); GND dikiş viaları,
  F/B GND dolgu
- Şema üretildi; şemadan çıkan netlist kartla **pin pin aynı**
- Kırmızı lehim maskesi + ENIG stackup'ta tanımlı

**Kalan iş**
- KiCad DRC'de birkaç güç bağlantısı kalıyor (bkz. `kicad/build/drc.rpt`, `make` ile üretilir) —
  KiCad'de açıp ratsnest'e bakarak elle tamamlanabilir
- İpek baskı yazılarının yerleşimi (uyarı seviyesinde)
- Sipariş öncesi "Doğrulanacaklar" listesi

## Güç topolojisi

```
XT60 -> F1 -> Q1 ters polarite -> RS1 shunt (INA226) -> VSYS
                                                        |
                    +-------------------+---------------+-----------------+
                    |                   |                                 |
               J3 klemens         U7 5V BEC 3A                     Q2 ACIL STOP
               (Gemstone)          |       |                            |
                              servo rayı  U6 3V3 LDO           VBAT_SW -> DRV8874 x2
                              LED, enkoder  -> ESP32, mantık
```

Q2 arızada **kapalıdır**: gate VSYS'e pull-up'lı. Motorlar ancak ESP32 Q3'ü sürerken
**ve** J12'deki NC acil stop butonu kapalıyken güç alır. Ayrıntı:
[docs/03-guc-mimarisi.md](docs/03-guc-mimarisi.md).

## Doğrulanacaklar (sipariş öncesi)

1. **Gemstone DC giriş aralığı** — 5–9 V mı 5–12 V mi? (T3'e sor / e-fuse MPN'ine bak)
2. **40-pin header konumu** — el yapımı Fritzing parçasından ölçüldü, kumpasla teyit et
3. **Montaj delikleri** — layout PDF'inde MH1..MH7 var, Fritzing sadece 4'ünü çiziyor
4. **Stacking header yüksekliği** — Gemstone'un üst yüzeyindeki en yüksek eleman ölçülmeli
5. **Kamera kesiti** — `CUT` değerleri fotoğraftan tahmin
6. **DRV8874 pinout'u** — KiCad kütüphanesinde yok; TI veri sayfasıyla bir kez daha karşılaştır
7. **XT60 cinsiyeti** — kart tarafı bataryanın fişinin karşılığı olmalı (BOM: dişi)
