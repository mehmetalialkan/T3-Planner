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

Modül: **ESP32-S3-WROOM-1-N8R2**
> N8R8 (octal PSRAM) ALMA — GPIO33–37'yi kullanılamaz hale getirir.

| Fonksiyon | GPIO | Not |
|---|---|---|
| Motor A — PH (yön) | 4 | DRV8874 |
| Motor A — EN (PWM) | 5 | LEDC/MCPWM |
| Motor B — PH | 6 | |
| Motor B — EN (PWM) | 7 | |
| Sürücü nSLEEP (ortak) | 15 | düşük = motorlar serbest |
| Sürücü nFAULT (ortak) | 16 | açık drenaj, pull-up gerekir |
| Akım geri besleme A | 1 | ADC1_CH0, IPROPI |
| Akım geri besleme B | 2 | ADC1_CH1, IPROPI |
| Enkoder A — kanal A / B | 8 / 9 | PCNT birimi 0 |
| Enkoder B — kanal A / B | 10 / 11 | PCNT birimi 1 |
| I2C SDA / SCL | 41 / 42 | 4.7k pull-up |
| Host UART TX / RX | 47 / 48 | 921600 baud |
| WS2812 durum LED | 40 | 4 adet zincir |
| Acil stop butonu | 18 | giriş, pull-up |
| Acil stop röle sürücü | 21 | çıkış |
| Bumper 1 / 2 | 38 / 39 | giriş, pull-up |
| Genel amaçlı header | 12, 13, 14, 17 | takıma açık |
| Debug konsol UART0 | 43 / 44 | USB-C ile paylaşımlı |
| BOOT butonu | 0 | strapping |
| USB D− / D+ | 19 / 20 | USB-C, flaşlama |
| **KULLANMA** | 26–37 | dahili flash/PSRAM |

## 3. I2C adres haritası (ESP32 veri yolu)

| Cihaz | Adres | İşlev |
|---|---|---|
| PCA9685 | 0x40 | 16 kanal servo PWM |
| INA226 | 0x45 | batarya gerilim + akım |
| SSD1306 OLED | 0x3C | IP / batarya / mod göstergesi |
| VL53L0X | 0x29 | opsiyonel ToF |
| Qwiic | boş | takım genişletmesi |

> PCA9685 ve INA226'nın ikisi de fabrika çıkışı 0x40'tır. INA226'nın A0
> pinini VS'e çekerek 0x45'e al, yoksa veri yolu çakışır.
