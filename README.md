# IronGate Lab

[![CI](https://github.com/Muhammet0-1/IronGate/actions/workflows/ci.yml/badge.svg)](https://github.com/Muhammet0-1/IronGate/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Lisans: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

IronGate Lab; temel ICS/SCADA süreç izleme, kontrol durumu değişiklikleri ve arıza emniyetli
yazılım tasarımı konularını incelemek için yalnızca **localhost üzerinde çalışan** bir Modbus/TCP
eğitim ortamıdır.
Sentetik su basıncı süreci, küçük bir PLC simülatörü ve sınırlı bir senaryo çalıştırıcısı içerir.

Proje bilinçli olarak bir laboratuvar aracıdır. Cihaz keşfetmez, gerçek endüstriyel sistemleri hedef
almaz, etkinliği gizlemez, kimlik bilgisi toplamaz ve zararlı yazılım davranışı uygulamaz.

## Projenin hikâyesi

İlk PoC, IronGate adını 2016 tarihli bir endüstriyel kontrol zararlısı hakkındaki kamuya açık
araştırmalara gönderme olarak kullanıyordu. Bu erken sürüm, bir simülatörü otonom register yazma
betiğiyle birleştiriyor ve gösterimi saldırı odaklı terimlerle açıklıyordu.

0.2.0 sürümü bu fikri savunma amaçlı bir mühendislik laboratuvarı olarak yeniden kurar. Bağlantılar
kod içinde loopback adresleriyle sınırlandırılmıştır, varsayılan davranış gözlemdir, yazma modu sonlu
ve tam endpoint onayına bağlıdır; yalnız sentetik vana için kullanılan `1` numaralı register
yazılabilir. Analizden kaçınma ve gizlenme davranışları özellikle dahil edilmemiştir.

## Güvenlik sınırları

- İstemci ve sunucu yalnızca `localhost`, `127.0.0.0/8` veya `::1` kabul eder.
- Loopback sınırlamasını kapatan bir seçenek yoktur.
- Simülatör varsayılan olarak ayrıcalıksız `5020` portunu kullanır.
- `observe` hiçbir zaman register yazmaz.
- `scenario`, `--apply` verilmedikçe yalnızca gözlem yapar.
- Yazma modu ayrıca `--confirm-lab-target` değerinin tam endpoint ile eşleşmesini ister.
- Her çalıştırmanın iterasyon sayısı sınırlıdır; üst sınır 1.000'dir.
- Yalnızca sentetik vana komutuna ait `1` numaralı register yazılabilir.
- Çalıştırıcının açtığı vana, mümkün olduğunda temizleme işlemi sırasında kapatılır.
- Gerçek ağ taraması, kalıcılık, işlem enjeksiyonu, anti-VM veya gizlenme özelliği yoktur.

Bu kontroller kazara kötüye kullanım riskini azaltır; Modbus/TCP protokolünü güvenli hâle getirmez.
Benzer araçları hiçbir zaman sahibi olmadığınız ve açık test izniniz bulunmayan ekipmanlara yöneltmeyin.

## Mimari

```text
irongate-lab scenario/observe
            |
            v
   doğrulanmış loopback endpoint
            |
            v
   PyModbus geçidi ----> localhost Modbus/TCP sunucusu
                                    |
                                    v
                           thread-safe register bankası
                                    |
                                    v
                           sentetik basınç süreci
```

Etki alanı modeli ve senaryo politikası PyModbus'tan bağımsızdır; bu nedenle testlerin neredeyse
tamamı soket açmadan çalışır.

## Gereksinimler

- Python 3.10 veya üzeri
- PyModbus 3.11.x (tek bir minor API serisine sabitlenmiştir)

## Kurulum

```bash
git clone https://github.com/Muhammet0-1/IronGate.git
cd IronGate

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Geliştirme araçları için:

```bash
python -m pip install -e '.[dev]'
```

## Hızlı başlangıç

Bir terminalde sentetik PLC'yi başlatın:

```bash
irongate-lab simulate
```

Başka bir terminalden beş durum görüntüsü okuyun; bu komut yazma yapmaz:

```bash
irongate-lab observe --iterations 5
```

Sınırlı yerel yazma gösterimini çalıştırın:

```bash
irongate-lab scenario \
  --iterations 15 \
  --open-below 55 \
  --close-at 65 \
  --apply \
  --confirm-lab-target 127.0.0.1:5020
```

Makine tarafından okunabilir çıktı için `--json` kullanılabilir:

```bash
irongate-lab observe --iterations 3 --json
```

Eski dosya adları güvenli uyumluluk sarmalayıcıları olarak korunur:

```bash
python plc_sim.py
python irongate.py --iterations 5
```

## Register haritası

| Adres | Ad | Erişim | Değerler |
| ---: | --- | --- | --- |
| `0` | Basınç | Salt okunur | `0`–`150` arasında sentetik değer |
| `1` | Vana komutu | Okuma/yazma | `0` kapalı, `1` açık |
| `2` | Alarm | Salt okunur | `0` normal, `1` yüksek basınç |

Harita bilinçli olarak küçüktür ve herhangi bir üreticinin gerçek cihazını temsil etmez.

## CLI referansı

```bash
irongate-lab --help
irongate-lab simulate --help
irongate-lab observe --help
irongate-lab scenario --help
```

Geçersiz host değerleri, ayrıcalıklı portlar, sonlu olmayan zaman değerleri, geçersiz cihaz
kimlikleri ve onaylanmamış yazma işlemleri açık bir yapılandırma hatasıyla durdurulur.

## Geliştirme ve doğrulama

```bash
ruff check .
mypy
pytest
python -m build
```

GitHub Actions matrisi bu kontrolleri Python 3.10, 3.11, 3.12 ve 3.13 üzerinde çalıştırır. Testler
sahte taşıma katmanları ve deterministik bozucu etkiler kullanır; harici sistemlere bağlanmaz.

## Sorumlu kullanım

Bu projeyi yalnızca yerel bir eğitim simülatörü veya kod inceleme çalışması olarak kullanın. Projeyle
ilgili güvenlik bildirimleri için [SECURITY.md](SECURITY.md), katkı rehberi için
[CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## Lisans

[MIT Lisansı](LICENSE) ile yayımlanmıştır.
