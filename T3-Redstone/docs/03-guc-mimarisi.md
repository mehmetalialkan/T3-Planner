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
        ┌──────────────── Redstone ────────────────┐
XT60 ───┤ F1 sigorta ── Q1 ters polarite (ideal    │
 2S     │               diyot P-MOSFET)            │
LiPo    │        │                                 │
        │        ├── PASSTHROUGH ──────────────────┼──> Gemstone yeşil klemens (+/-)
        │        │   (her zaman açık, 5A)          │     pigtail, 18AWG
        │        │                                 │
        │        ├── INA226 shunt ── K1 ACIL STOP ─┼──> DRV8874 x2 (motorlar)
        │        │                     rölesi      │
        │        │                                 │
        │        ├── 5V BEC (3A) ─────────────────┼──> servo rayı (PCA9685 çıkışları)
        │        │                                 │
        │        └── AP2112K 3V3 ─────────────────┼──> ESP32-S3, mantık
        └──────────────────────────────────────────┘
```

## 3. Kurallar

1. **Yıldız noktası sigortanın hemen ardında.** Motor akımı SBC'nin besleme
   hattından geçmeyecek — geçerse stall anında gerilim sarkması karta yansır.
2. **Acil stop yalnızca motor kolunda.** SBC'nin gücü asla kesilmez; kesilirse
   her acil durdurma Linux'u çökertir ve eMMC'yi riske atar.
3. **Servo rayı SBC ile paylaşılmaz.** Servo akım darbesi ayrı BEC'te kalır.
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
