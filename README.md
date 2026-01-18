# 🏭 IronGate - ICS/SCADA Security Research

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![SCADA](https://img.shields.io/badge/Protocol-Modbus%20TCP-orange?style=for-the-badge)

**IronGate**, endüstriyel kontrol sistemlerine (ICS) yönelik siber saldırı ve savunma senaryolarını simüle etmek için geliştirilmiş bir **PoC (Proof of Concept)** çerçevesidir.

Proje, 2016 yılında keşfedilen *IronGate* zararlı yazılımının çalışma mantığından (özellikle Anti-VM teknikleri ve PLC manipülasyonu) esinlenmiştir.

## 🏗️ Mimari

Proje iki ana bileşenden oluşur:

### 1. PLC Simulator (`plc_sim.py`)
Sanal bir su basınç tesisini simüle eden Modbus TCP Sunucusu.
* **Fonksiyon:** Basınç değerlerini, vana durumlarını ve alarmları yönetir.
* **Protokol:** Modbus TCP (Port 5020).
* **Register Map:** Holding Registerlar üzerinden sensör verisi okur/yazar.

### 2. IronGate Agent (`irongate.py`)
Hedef PLC'ye bağlanarak süreç manipülasyonu yapan saldırı scripti.
* **False Data Injection:** Basınç değerlerini manipüle ederken, operatöre (simüle edilmiş) sahte normal veriler göstermeyi hedefler.
* **Anti-VM:** Çalıştığı ortamın sanal olup olmadığını analiz eder (Linux sysfs kontrolü).
* **Sabotaj:** Vana kontrol registerlarını (Coil/Register) manipüle ederek sistemi kritik seviyeye sürükler.

## 🚀 Kurulum ve Test

```bash
# Bağımlılıkları yükleyin
pip install pymodbus

# Terminal 1: Santrali Başlat
python plc_sim.py

# Terminal 2: Saldırıyı Başlat
python irongate.py

⚠️ Yasal Uyarı

Bu proje sadece eğitim ve akademik araştırma amaçlıdır. Gerçek endüstriyel sistemlerde (OT/SCADA) izinsiz test yapmak, ciddi fiziksel hasarlara ve yasal yaptırımlara yol açabilir.
Sadece kendi laboratuvar ortamınızda kullanın.