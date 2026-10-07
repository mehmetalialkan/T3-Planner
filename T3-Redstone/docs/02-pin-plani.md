# T3-Redstone — Pin Planı

## 1. Host tarafı: 40-pin header kullanımı

Redstone header'dan sadece **4 sinyal pini** tüketir. Geri kalan 24 GPIO takıma kalır.

| HAT pini | Fiziksel pin | Kullanım | Linux |
|---|---:|---|---|
| GPIO-14 | 8 | UART-MAIN1 TXD → ESP32 RX | `/dev/ttyS3` |
| GPIO-15 | 10 | UART-MAIN1 RXD ← ESP32 TX | `/dev/ttyS3` |
| GPIO-27 | 13 | Acil stop durumu (giriş, host okur) | GPIO |
| GPIO-26 | 37 | Buzzer | GPIO |
| 5V | 2, 4 | **bağlanmayacak** — güç pigtail ile klemense gider | — |
| GND | 6,9,14,20,25,30,34,39 | hepsi bağlanır | — |

Gerekli overlay: `k3-am67a-t3-gem-o1-uart-ttys3.dtbo`

> **Çakışma uyarısı:** `k3-am67a-t3-gem-o1-pwm-epwm0-gpio5-gpio14.dtbo` overlay'i
> GPIO-14'ü PWM'e alır ve UART-MAIN1 TX'i öldürür. Bu overlay AÇILMAMALI.

### Takıma kalan kaynaklar
| Kaynak | Pinler |
|---|---|
| I2C-MCU0 | GPIO-2 / GPIO-3 (pin 3, 5) |
| **I2C4 (ikinci I2C — dokümanlarda geçmiyor)** | GPIO-22 / GPIO-25 (pin 15, 22) |
| SPI-MCU0 + CS0/CS2 | GPIO-9/10/11/8/7 |
| PWM (bağımsız periyot) | ECAP0 GPIO-12, ECAP1 GPIO-16, ECAP2 GPIO-18 |
| PWM (periyot çifti bağlı) | GPIO-5+GPIO-14 · GPIO-6+GPIO-13 |
| EQEP0 enkoder | GPIO-16 (A) / GPIO-17 (B) |
| EQEP1 enkoder | GPIO-18 (A) / GPIO-19 (B) |

## 2. ESP32-S3 pin atama

Modül: **ESP32-S3-WROOM-1U-N8R2** (U.FL anten konnektörü modülün üstünde)
> N8R8 (octal PSRAM) ALMA — GPIO33–37'yi kullanılamaz hale getirir.

Pinler kartın **coğrafyasına göre** dağıtıldı: ESP32-S3'te LEDC/MCPWM, PCNT ve UART
GPIO matrisiyle her pine atanabildiği için, sürücülere giden sinyaller modülün alt
sırasından, enkoder/I2C sağ kenarından, host ve konnektör sinyalleri sol kenarından
çıkar. (Rev A'da motor sinyalleri sol kenardaydı ve kartı boydan boya dolaşıyordu.)

| Fonksiyon | GPIO | Modül pini | Not |
|---|---|---|---|
| Host UART TX → Gemstone RX (pin 10) | 4 | 4 | 921600 baud |
| Host UART RX ← Gemstone TX (pin 8) | 5 | 5 | |
| Acil stop döngüsü (ESTOP_LOOP) | 6 | 6 | giriş; 0 = NC buton kapalı (normal), 1 = basılı / kablo kopuk |
| Bumper 1 / 2 | 7 / 15 | 7 / 8 | giriş, dahili pull-up |
| GPIO header J14 | 16 / 17 | 9 / 10 | 3V3 / IO16 / IO17 / GND |
| USB D− / D+ | 19 / 20 | 13 / 14 | USB-C, flaşlama + konsol (USB-Serial/JTAG) |
| Motor A — PH (yön) / EN (PWM) | 9 / 10 | 17 / 18 | DRV8874 U2 |
| Motor B — PH / EN | 11 / 12 | 19 / 20 | DRV8874 U3 |
| Sürücü nSLEEP (ortak) | 13 | 21 | düşük = motorlar serbest |
| Sürücü nFAULT (ortak) | 14 | 22 | açık drenaj, 10 k pull-up |
| Acil stop sürücü (ESTOP_DRV) | 21 | 23 | 1 = motor gücünü aç; 100 k pull-down → reset'te kapalı |
| SK6812MINI veri | 47 | 24 | 74AHCT1G125 ile 5 V'a çevrilir |
| INA226 ALERT | 48 | 25 | 10 k pull-up |
| BOOT butonu | 0 | 27 | strapping |
| Enkoder A — kanal A / B | 38 / 39 | 31 / 32 | PCNT birimi 0 |
| Enkoder B — kanal A / B | 40 / 41 | 33 / 34 | PCNT birimi 1 |
| I2C SDA / SCL | 42 / 44 | 35 / 36 | 4.7 k pull-up (IO44 = U0RXD, boot'ta giriş) |
| Acil stop durumu → host (pin 13) | 43 | 37 | U0TXD: boot sırasında ROM log'u basar, host bu süreyi yok saymalı |
| Akım geri besleme A / B | 1 / 2 | 39 / 38 | ADC1_CH0 / CH1, IPROPI |
| Boş | 8, 18 | 12, 11 | yedek |
| Bağlı değil (strap) | 3, 45, 46 | 15, 26, 16 | boot strap pinleri |
| **KULLANMA** | 35–37 | 28–30 | PSRAM ile paylaşımlı |

## 3. I2C adres haritası (ESP32 veri yolu)

| Cihaz | Adres | İşlev |
|---|---|---|
| PCA9685 | 0x40 | 16 kanal servo PWM |
| INA226 | 0x45 | batarya gerilim + akım |
| SSD1306 OLED | 0x3C | Qwiic (J10) üzerinden, opsiyonel |
| VL53L0X | 0x29 | Qwiic üzerinden, opsiyonel ToF |
| Qwiic | boş | takım genişletmesi |

> PCA9685 ve INA226'nın ikisi de varsayılan olarak 0x40'tır. INA226'da **A0 ve A1'in
> ikisi de VS'e** bağlıdır → 0x45 (yalnız A0=VS olsaydı 0x41 olurdu).
