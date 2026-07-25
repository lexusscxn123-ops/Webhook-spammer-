"""
FPS Mechanics Lab - Ana Uygulama
CS2 Teknik Analiz Simülatörü
"""

import sys
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict
import threading
import time

# Proje modülleri
from core.memory_reader import MemoryReader
from core.entity_manager import EntityManager
from core.offsets import OffsetManager
from core.signature_scanner import SignatureScanner
from math.w2s import world_to_screen_numba
from esp.overlay_pyqt import ESPOverlay
from radar.radar_window import RadarWindow
from aimbot.aimbot_core import AimbotCore
from aimbot.triggerbot import Triggerbot
from aimbot.rapidfire import Rapidfire
from security.anti_cheat_analysis import AntiCheatAnalysis
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.performance import PerformanceMonitor

logger = setup_logger(__name__)

class FPSMechanicsLab:
    """
    Ana uygulama sınıfı
    Tüm modülleri başlatır ve yönetir
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        FPSMechanicsLab başlatıcısı
        
        Args:
            config_path: Konfigürasyon dosyası yolu
        """
        self.config_path = config_path
        self.config = None
        self.running = False
        
        # Modüller
        self.memory_reader = None
        self.entity_manager = None
        self.offset_manager = None
        self.signature_scanner = None
        self.esp_overlay = None
        self.radar_window = None
        self.aimbot = None
        self.triggerbot = None
        self.rapidfire = None
        self.security_analyzer = None
        self.performance_monitor = None
        
        # Thread'ler
        self.threads = []
        
        # Veriler
        self.view_matrix = None
        self.local_player = None
        self.entities = []
        
        logger.info("FPS Mechanics Lab başlatılıyor...")
        
        # Konfigürasyonu yükle
        self.load_config()
        
        # Offset yöneticisini başlat
        self.offset_manager = OffsetManager(self.config_path)
        
        # Signature scanner
        self.signature_scanner = SignatureScanner()
        
        # Performans monitörü
        self.performance_monitor = PerformanceMonitor()
        
        # Güvenlik analizörü
        self.security_analyzer = AntiCheatAnalysis()
        
    def load_config(self):
        """Konfigürasyon dosyasını yükler"""
        try:
            config_manager = ConfigManager(self.config_path)
            self.config = config_manager.load_config()
            logger.info("Konfigürasyon başarıyla yüklendi")
        except Exception as e:
            logger.error(f"Konfigürasyon yüklenemedi: {e}")
            sys.exit(1)
    
    def initialize_memory(self) -> bool:
        """
        Bellek okuyucuyu başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            self.memory_reader = MemoryReader("cs2.exe")
            if not self.memory_reader.connect():
                logger.error("CS2 prosesine bağlanılamadı!")
                return False
            
            # Offset'leri güncelle
            if not self.offset_manager.update_offsets(self.memory_reader, self.signature_scanner):
                logger.warning("Offsets güncellenemedi, mevcut offset'ler kullanılacak")
            
            # Entity manager'ı başlat
            self.entity_manager = EntityManager(
                self.memory_reader, 
                self.offset_manager.get_all_offsets()
            )
            
            logger.info("Bellek modülü başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Bellek başlatma hatası: {e}")
            return False
    
    def initialize_esp(self) -> bool:
        """
        ESP overlay'ini başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            from PyQt5.QtWidgets import QApplication
            
            # PyQt5 uygulaması başlat (eğer başlatılmadıysa)
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
            
            # View matrix getter fonksiyonu
            def get_view_matrix():
                if self.view_matrix is not None:
                    return self.view_matrix
                
                # View matrix'i oku
                offset = self.offset_manager.get_offset('dwViewMatrix')
                if offset and self.memory_reader:
                    matrix_addr = self.memory_reader.module_base + offset
                    matrix = self.memory_reader.read_matrix_4x4(matrix_addr)
                    if matrix:
                        self.view_matrix = matrix
                        return matrix
                return None
            
            # ESP overlay
            self.esp_overlay = ESPOverlay(
                self.entity_manager,
                get_view_matrix,
                screen_width=1920,
                screen_height=1080
            )
            
            logger.info("ESP overlay başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"ESP başlatma hatası: {e}")
            return False
    
    def initialize_radar(self) -> bool:
        """
        Radar'ı başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            if self.config['radar_settings']['enabled']:
                self.radar_window = RadarWindow(
                    self.entity_manager,
                    map_name="de_dust2",  # Harita tespiti yapılabilir
                    width=400,
                    height=400
                )
                logger.info("Radar başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Radar başlatma hatası: {e}")
            return False
    
    def initialize_aimbot(self) -> bool:
        """
        Aimbot'u başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            if self.config['aimbot_settings']['enabled']:
                self.aimbot = AimbotCore(
                    self.entity_manager,
                    self.memory_reader,
                    self.offset_manager.get_all_offsets(),
                    self.config['aimbot_settings']
                )
                logger.info("Aimbot başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Aimbot başlatma hatası: {e}")
            return False
    
    def initialize_triggerbot(self) -> bool:
        """
        Triggerbot'u başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            self.triggerbot = Triggerbot(
                self.entity_manager,
                self.memory_reader,
                self.offset_manager.get_all_offsets()
            )
            logger.info("Triggerbot başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Triggerbot başlatma hatası: {e}")
            return False
    
    def initialize_rapidfire(self) -> bool:
        """
        Rapidfire'ı başlatır
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            self.rapidfire = Rapidfire(
                self.memory_reader,
                self.offset_manager.get_all_offsets()
            )
            logger.info("Rapidfire başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Rapidfire başlatma hatası: {e}")
            return False
    
    def start(self):
        """
        Uygulamayı başlatır
        """
        logger.info("FPS Mechanics Lab başlatılıyor...")
        
        # Memory başlat
        if not self.initialize_memory():
            logger.error("Memory başlatılamadı, uygulama kapatılıyor...")
            return
        
        # ESP başlat
        if not self.initialize_esp():
            logger.warning("ESP başlatılamadı")
        
        # Radar başlat
        if not self.initialize_radar():
            logger.warning("Radar başlatılamadı")
        
        # Aimbot başlat
        if not self.initialize_aimbot():
            logger.warning("Aimbot başlatılamadı")
        
        # Triggerbot başlat
        if not self.initialize_triggerbot():
            logger.warning("Triggerbot başlatılamadı")
        
        # Rapidfire başlat
        if not self.initialize_rapidfire():
            logger.warning("Rapidfire başlatılamadı")
        
        # Background thread'leri başlat
        self.start_background_threads()
        
        # Ana döngü
        self.running = True
        self.main_loop()
    
    def start_background_threads(self):
        """Background thread'leri başlatır"""
        # Entity güncelleme thread'i
        update_thread = threading.Thread(target=self.update_entities_loop, daemon=True)
        update_thread.start()
        self.threads.append(update_thread)
        
        # Aimbot thread'i
        if self.aimbot:
            aimbot_thread = threading.Thread(target=self.aimbot_loop, daemon=True)
            aimbot_thread.start()
            self.threads.append(aimbot_thread)
        
        # Triggerbot thread'i
        if self.triggerbot:
            trigger_thread = threading.Thread(target=self.triggerbot_loop, daemon=True)
            trigger_thread.start()
            self.threads.append(trigger_thread)
        
        logger.info(f"{len(self.threads)} background thread başlatıldı")
    
    def update_entities_loop(self):
        """Entity'leri güncelleme döngüsü"""
        while self.running:
            try:
                with self.performance_monitor.measure_time("entity_update"):
                    if self.entity_manager:
                        self.entity_manager.update()
                        self.entities = self.entity_manager.entities
                        self.local_player = self.entity_manager.local_player
                    
                    # View matrix'i güncelle
                    if self.memory_reader and self.offset_manager:
                        offset = self.offset_manager.get_offset('dwViewMatrix')
                        if offset:
                            matrix_addr = self.memory_reader.module_base + offset
                            matrix = self.memory_reader.read_matrix_4x4(matrix_addr)
                            if matrix:
                                self.view_matrix = matrix
                
                time.sleep(0.01)  # ~100 FPS güncelleme
                
            except Exception as e:
                logger.error(f"Entity güncelleme hatası: {e}")
                time.sleep(0.1)
    
    def aimbot_loop(self):
        """Aimbot döngüsü"""
        while self.running and self.aimbot:
            try:
                with self.performance_monitor.measure_time("aimbot"):
                    self.aimbot.update()
                time.sleep(0.005)  # ~200 FPS
            except Exception as e:
                logger.error(f"Aimbot hatası: {e}")
                time.sleep(0.1)
    
    def triggerbot_loop(self):
        """Triggerbot döngüsü"""
        while self.running and self.triggerbot:
            try:
                with self.performance_monitor.measure_time("triggerbot"):
                    self.triggerbot.update()
                time.sleep(0.01)  # ~100 FPS
            except Exception as e:
                logger.error(f"Triggerbot hatası: {e}")
                time.sleep(0.1)
    
    def main_loop(self):
        """Ana uygulama döngüsü"""
        try:
            # PyQt5 uygulama döngüsü
            if hasattr(self, 'app') and self.app:
                self.app.exec_()
            else:
                # Konsol modu
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("Uygulama kullanıcı tarafından durduruldu")
        except Exception as e:
            logger.error(f"Ana döngü hatası: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Kaynakları temizler"""
        self.running = False
        
        # Thread'leri bekle
        for thread in self.threads:
            try:
                thread.join(timeout=1.0)
            except:
                pass
        
        # Modülleri kapat
        if self.memory_reader:
            self.memory_reader.close()
        
        if self.esp_overlay:
            self.esp_overlay.close()
        
        if self.radar_window:
            self.radar_window.close()
        
        # Performans raporu
        if self.performance_monitor:
            self.performance_monitor.print_report()
        
        logger.info("Uygulama kapatıldı")

def main():
    """
    Uygulama giriş noktası
    """
    # Log seviyesini ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # FPS Mechanics Lab'ı başlat
    lab = FPSMechanicsLab()
    
    # Anti-cheat analizi yap (eğitim amaçlı)
    logger.info("🔒 Anti-cheat analizi başlatılıyor...")
    security_report = lab.security_analyzer.generate_security_report()
    with open("security_report.html", "w", encoding="utf-8") as f:
        f.write(security_report)
    logger.info("Güvenlik raporu oluşturuldu: security_report.html")
    
    # Uygulamayı başlat
    lab.start()

if __name__ == "__main__":
    main()
