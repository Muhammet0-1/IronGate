import logging
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading
import time
import random

# === SANAL SU BASINÇ TESİSİ SİMÜLATÖRÜ ===
# Register Adresleri:
# 40001: Basınç Değeri (0-100 Bar)
# 40002: Vana Durumu (0: Kapalı, 1: Açık)
# 40003: Alarm Durumu (0: Güvenli, 1: TEHLİKE)

class PLCSimulator:
    def __init__(self):
        self.pressure = 50  # Başlangıç basıncı (Bar)
        self.valve_open = False
        self.alarm = False
        
        # Modbus Hafıza Bloğu Oluştur (Registerlar)
        # 0x00 ile başlatıyoruz
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*100),
            co=ModbusSequentialDataBlock(0, [0]*100),
            hr=ModbusSequentialDataBlock(0, [0]*100), # Holding Registers (En önemlisi)
            ir=ModbusSequentialDataBlock(0, [0]*100))
        
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def process_logic(self):
        """
        PLC'nin fiziksel dünyayı simüle ettiği döngü.
        Basınç değişimini ve alarm durumlarını yönetir.
        """
        print("[PLC] Tesis Simülasyonu Başladı...")
        while True:
            # 1. Mevcut Değerleri Hafızadan Oku
            # Register 0 (40001 aslında 0. indextir)
            register_values = self.store.getValues(3, 0, count=5) # 3 = Holding Register
            
            # Dışarıdan müdahale (Hacker) var mı diye register'ı kontrol et
            # Hacker register'ı değiştirebilir, biz de onu okuruz.
            current_pressure_setting = register_values[0]
            
            # 2. Fiziksel Simülasyon
            # Basıncı doğal olarak biraz dalgalandır (Sensör gürültüsü)
            fluctuation = random.randint(-2, 2)
            self.pressure = max(0, min(150, self.pressure + fluctuation))
            
            # Eğer hacker vana registerını (index 1) 1 yaptıysa basıncı artır
            if register_values[1] == 1:
                self.pressure += 5 # Hızla artış
                print(f"[PLC] UYARI: Vana AÇIK! Basınç artıyor: {self.pressure} Bar")
            else:
                # Vana kapalıysa basınç yavaşça normale döner (50 Bar)
                if self.pressure > 50: self.pressure -= 2
                if self.pressure < 50: self.pressure += 2

            # 3. Alarm Kontrolü
            if self.pressure > 90:
                self.alarm = True
                print(f"[PLC] ALARM: KRİTİK BASINÇ SEVİYESİ! ({self.pressure} Bar)")
                # Alarm registerını (index 2) 1 yap
                self.store.setValues(3, 2, [1])
            else:
                self.alarm = False
                self.store.setValues(3, 2, [0])

            # 4. Yeni Değerleri Hafızaya Yaz (Sensör verisi güncelleme)
            # Hacker bu değeri okuyacak
            self.store.setValues(3, 0, [self.pressure])
            
            time.sleep(1)

    def run_server(self):
        # Simülasyon thread'ini başlat
        sim_thread = threading.Thread(target=self.process_logic)
        sim_thread.daemon = True
        sim_thread.start()
        
        # Modbus TCP Server'ı Başlat (Port 5020 kullanacağız, root olmamak için)
        print("[PLC] Modbus TCP Sunucusu 0.0.0.0:5020 üzerinde dinliyor...")
        StartTcpServer(context=self.context, address=("0.0.0.0", 5020))

if __name__ == "__main__":
    plc = PLCSimulator()
    plc.run_server()
