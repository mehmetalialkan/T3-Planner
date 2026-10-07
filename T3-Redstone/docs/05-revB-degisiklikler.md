# Rev B — bulunan hatalar ve yapılan değişiklikler

Rev A'daki bütün entegre pinleri KiCad'in resmi sembol kütüphanesiyle (DRV8874 için TI veri
sayfasıyla) tek tek karşılaştırıldı. Aşağıdaki hataların çoğu kartı **çalışmaz** hale
getiriyordu; bir kısmı parçaya ya da Gemstone'a zarar verebilirdi.

## Kritik — kart çalışmazdı / zarar görürdü

| # | Yer | Rev A | Rev B |
|---|---|---|---|
| 1 | **INA226** (U5) | Pin tablosu tamamen yanlış: pin 7 (gerçekte GND) +3V3'e bağlı → **3V3 kısa devre**; pin 4 (SDA) GND'ye → bütün I2C hattı ölü; adres pinleri (1, 2) bataryaya | 1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN−, 10 IN+ |
| 2 | **PCA9685** (U4) | Adres pinleri 1–6 sanılmış: pin 6 (LED0 çıkışı) GND'ye kısa; servo kanalları bir pin kaymış; OE̅ (pin 23) servo header'ına gidiyordu → çıkışlar rastgele kapanır | LED0..7 = pin 6..13, LED8..15 = pin 15..22, OE̅ = 23, A5 = 24 |
| 3 | **DRV8874** (U2, U3) | Pinout uydurma: 2× VM, 2× PGND, 2× OUT varsayılmış. Şarj pompası (CPH/CPL/VCP) ve IMODE hiç yok | TI SLVSF66 pin tablosu; CPH–CPL 22 nF, VCP–VM 100 nF eklendi; PMODE = GND (PH/EN), IMODE = GND |
| 4 | **Acil stop FET** (Q2) | P-FET ters: source motor tarafında, drain VSYS'te → gövde diyodu motoru **her zaman** besliyordu, acil stop hiçbir şeyi kesmiyordu | S = VSYS, D = VBAT_SW |
| 5 | **Host UART** | Gemstone TXD (pin 8) ESP32'nin TX'ine (IO47) bağlı: TX ↔ TX çakışması | pin 8 → IO48 (ESP RX), pin 10 ← IO47 (ESP TX) |
| 6 | **ESP32 pinleri** | Enkoder B1/A2/B2 yanlış pad'lerde; bumper IO36/IO37'de (PSRAM bölgesi, pin planı "KULLANMA" diyor); LED IO38'de; acil stop butonu IO39'da | Sinyaller kartın coğrafyasına göre yeniden atandı (sürücüler alt sıradan, enkoder/I2C sağdan, host solda) — [02-pin-plani.md](02-pin-plani.md) |
| 7 | **Durum LED'leri** | WS2812B'lerin VDD ve GND pinleri **bağlı değildi**; 3.3 V veri 5 V LED'in eşiğinin altında | SK6812MINI ×4, +5V ve GND bağlı, her birine 100 nF, 74AHCT1G125 ile 3.3 → 5 V veri |
| 8 | **5 V BEC** (U7) | FB bölücü 68k / 10k → **6.0 V** çıkış (AP2112K'nın girişi 6 V sınırında, enkoderler 5 V) | 56k / 10k → 5.07 V |
| 9 | **Diyotlar** D1, D2 | SOD-123'te pad 1 = katot olduğu hesaba katılmamış: D1 BEC'in 5 V'unu USB portuna basıyordu; D2 buzzer açılınca 3V3'ü kısa devre ediyordu | Yönler düzeltildi |
| 10 | **ESP32 EN** | RC gecikme kondansatörü yoktu → açılışta boot kararsız | 10 k + 1 µF |
| 11 | **Q3 gate** | Pull-down yoktu → ESP32 reset/boot sırasında acil stop FET'i tanımsız | 100 k pull-down: reset'te motor kapalı |
| 12 | **XT60** | Footprint 7.8 mm adımla çizilmişti (gerçek 7.2 mm) → konnektör takılmazdı | Resmi AMASS XT60 footprint'i |
| 13 | **ESP32-S3-WROOM-1U footprint'i** | Elle çizilmiş, pad dağılımı yanlış (15/9/15; gerçek 14/12/14) | Resmi `RF_Module:ESP32-S3-WROOM-1U` |
| 14 | **J9 U.FL** | Kartta ayrıca U.FL vardı ama hiçbir yere bağlı değildi — WROOM-1U'nun U.FL'si modülün üstünde | Kaldırıldı |

## Önemli iyileştirmeler

- **Donanımsal acil stop:** NC buton (J12) artık Q3'ün source'unda. Butona basılırsa ya da
  kablo koparsa ESP32 ne yaparsa yapsın motor gücü kesilir. Buton kullanılmayacaksa J12'ye köprü tak.
- **INA226 adresi:** A0 = VS tek başına 0x41 yapar. 0x45 için A0 = A1 = VS bağlandı.
  INA226 ALERT → ESP32 IO14 (10 k pull-up).
- **INA226 Kelvin bağlantısı:** IN+/IN− shunt pedlerinden ayrı yollarla alınıyor.
- **Enkoder girişleri:** 4×10 k pull-up dizisi (açık kollektörlü hall enkoderler için) +
  74LVC245 5 V → 3.3 V tampon.
- **USB ESD:** USBLC6-2SC6.
- **Buzzer 5 V** (BOM'daki manyetik 5 V buzzer ile uyumlu).
- **Footprint'lerin hepsi KiCad'in resmi kütüphanesinden** (servo 3×8 header hariç — o
  `kicad/T3RS.pretty`'de üretiliyor).
- **Şema eklendi:** `kicad/t3-redstone.kicad_sch` — `rs_design.py`'den üretilir; şemadan
  çıkan netlist kartla pin pin karşılaştırılır.

## Format

Kart KiCad 7 Python API'si (`pcbnew`) ile üretiliyor; dosyalar KiCad 7 biçiminde.
KiCad 8 / 9 bunları açar ve kaydederken kendi biçimine çevirir.
