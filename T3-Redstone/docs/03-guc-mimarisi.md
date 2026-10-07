# T3-Redstone — Güç Mimarisi

## 1. Karar: yalnızca 2S LiPo

Gemstone O1'in DC girişi için iki farklı resmî değer var:

| Kaynak | Aralık |
|---|---|
| Kart özellikleri sayfası | 5–12 V / 5 A |
| Blok diyagramı | **5–9 V** |

Bu çelişki çözülene kadar **3S (9.0–12.6 V) bağlanmaz.**
**2S LiPo = 6.0–8.4 V** her iki okumada da güvenli aralıkta.

## 2. Topoloji

```
XT60 ── F1 20A ── Q1 AO4407A ── RS1 2mΩ ──┬── VSYS ──────────────────────> J3: Gemstone DC girişi
 2S      sigorta   ters polarite  (INA226)  │          (her zaman açık)
LiPo               P-FET                    │
                                            ├── U7 TPS563201 ── +5V 3A ──┬─> servo rayı (J8A/J8B)
                                            │   (BEC)                    ├─> enkoder 5V, LED'ler
                                            │                            └─> U6 AP2112K ── +3V3 ──> ESP32, mantık
                                            │
                                            └── Q2 AO4407A (ACİL STOP) ── VBAT_SW ──> DRV8874 x2 (motorlar)
                                                 varsayılan KAPALI
USB-C 5V ── D1 B5819W ──> +5V   (yalnızca flaşlama; batarya yokken servoları USB'den besleme)
```

### Acil stop zinciri (donanım, yazılımdan bağımsız)

```
VSYS ── R6 100k ──┬── Q2 gate              Q2 KAPALI  ⇐  gate = VSYS
                  │
              Q3 drain                     Q2 AÇIK    ⇐  Q3 iletimde
              Q3 source ── J12 (NC buton) ── GND
              Q3 gate  ── ESTOP_DRV (ESP32 IO21) + R16 100k → GND
```

Motorlar ancak **ESP32 ESTOP_DRV=1 verdiğinde VE J12'deki NC buton kapalıyken** güç alır.
ESP32 reset atar/ölürse (R16), butona basılırsa ya da kablo koparsa motor gücü kesilir.
Buton kullanılmayacaksa J12'ye köprü takılmalı.

## 3. Kurallar

1. **Yıldız noktası sigortanın hemen ardında.** Motor akımı SBC'nin besleme
   hattından geçmeyecek — geçerse stall anında gerilim sarkması karta yansır.
2. **Acil stop yalnızca motor kolunda.** SBC'nin gücü asla kesilmez; kesilirse
   her acil durdurma Linux'u çökertir ve eMMC'yi riske atar. Servo rayı (BEC) da
   kesilmez — servolar acil stop'ta PCA9685 üzerinden yazılımla bırakılır.
3. **Servo rayı SBC ile paylaşılmaz.** Servo akım darbesi ayrı BEC'te kalır.
   BEC 3 A'dir: 16 servonun hepsi aynı anda yük altındaysa yetmez — büyük servolar
   için harici BEC ile servo rayını ayrı besle.
4. **Ters polarite koruması zorunlu.** Takımlar bataryayı ters takar; 3
   komponent karşılığında kartın en yüksek değerli bloğu.
5. **Düşük gerilim uyarısı.** INA226 6.4 V altını görünce ESP32 buzzer'ı öttürür
   ve host'a uyarı gönderir. 2S'in alt sınırı 6.0 V, Gemstone'un alt sınırı 5 V —
   arada 1 V pay var, ama stall sarkması bunu yer.

## 4. Neden kartta 5 V buck YOK

Gemstone'un DC girişi zaten regülatörlü (blok diyagramda "Main DC-DC Buck x2").
Ham 2S gerilimini doğrudan yiyor. 5 V üretmek:
- Layout'un en zor bloğunu (5 A buck) geri getirir,
- Aynı güç için %32 daha fazla akım demektir (25 W: 5 V'ta 5.0 A, 7.4 V'ta 3.4 A),
- Kartın alt sınırına (5 V) sıfır pay bırakır.

5 V veren batarya kimyası yoktur. **Batarya ne veriyorsa onu klemense ver.**

## 5. Kart üzerindeki dağıtım

| Katman | Görev |
|---|---|
| F.Cu | sinyal + yüksek akım dökümleri (XT60 → F1 → Q1 → RS1, Q2, motor çıkışları) |
| In1.Cu | kesintisiz GND düzlemi |
| In2.Cu | bölünmüş güç: VSYS (sol-alt), +5V (orta / sağ-üst), +3V3 (ESP32 bölgesi), VBAT_SW (motor bölgesi) |
| B.Cu | sinyal + GND dolgu; VSYS'i Q2'ye taşıyan 2 mm gövde (kamera kesitinin hemen üstü, y = 15.4 mm); LDO çıkışından orta ve sağ bölgedeki 3V3 tüketicilerine (PCA9685, INA226, 74LVC245, DRV8874 VREF, Qwiic) giden 0.4 mm +3V3 omurgası |

B.Cu'daki iki gövde bilerek orada: ESP32'den sürücülere giden sinyaller F.Cu'da ikisinin de üstünden via'sız geçer.

INA226 shunt'a **Kelvin** bağlıdır: RS1 dört uçlu bir shunt'tır (Vishay WSK2512, 2 mΩ).
Akım 1–4 pedlerinden geçer; IN+ / IN− (ve VBUS) ayrı ölçüm pedlerinden (2, 3) kendi
netleriyle (`SNS_P`, `SNS_N`) alınır, böylece bakır direnci ölçüme girmez.
