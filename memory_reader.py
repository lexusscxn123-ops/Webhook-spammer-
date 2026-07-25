"""
Memory Reader Modülü
CS2 bellek okuma işlemleri için temel sınıf
"""

import pymem
import pymem.process
import ctypes
from typing import Optional, Any
import struct
import logging
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class MemoryReader:
    """
    CS2 bellek okuyucu sınıfı
    Tüm bellek okuma işlemlerini yönetir
    """
    
    def __init__(self, process_name: str = "cs2.exe"):
        """
        MemoryReader başlatıcısı
        
        Args:
            process_name: Hedef proses adı (varsayılan: cs2.exe)
        """
        self.process_name = process_name
        self.pm = None
        self.client_dll = None
        self.engine2_dll = None
        self.module_base = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        CS2 prosesine bağlanır
        
        Returns:
            bool: Bağlantı başarılı ise True
        """
        try:
            logger.info(f"{self.process_name} prosesine bağlanılıyor...")
            self.pm = pymem.Pymem(self.process_name)
            
            # Modüllerin base adreslerini al
            self.client_dll = pymem.process.module_from_name(
                self.pm.process_handle, "client.dll"
            )
            self.engine2_dll = pymem.process.module_from_name(
                self.pm.process_handle, "engine2.dll"
            )
            
            if not self.client_dll or not self.engine2_dll:
                logger.error("client.dll veya engine2.dll bulunamadı!")
                return False
                
            self.module_base = self.client_dll.lpBaseOfDll
            self.is_connected = True
            logger.info(f"Bağlantı başarılı! client.dll: 0x{self.client_dll.lpBaseOfDll:X}")
            return True
            
        except pymem.exception.ProcessNotFound:
            logger.error(f"{self.process_name} bulunamadı! CS2 çalışıyor mu?")
            return False
        except Exception as e:
            logger.error(f"Bağlantı hatası: {e}")
            return False
    
    def read_int(self, address: int) -> Optional[int]:
        """
        Bellekten integer okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[int]: Okunan değer veya hata durumunda None
        """
        try:
            return self.pm.read_int(address)
        except Exception as e:
            logger.debug(f"read_int hatası (0x{address:X}): {e}")
            return None
    
    def read_float(self, address: int) -> Optional[float]:
        """
        Bellekten float okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[float]: Okunan değer veya hata durumunda None
        """
        try:
            return self.pm.read_float(address)
        except Exception as e:
            logger.debug(f"read_float hatası (0x{address:X}): {e}")
            return None
    
    def read_short(self, address: int) -> Optional[int]:
        """
        Bellekten short (2 byte) okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[int]: Okunan değer veya hata durumunda None
        """
        try:
            return self.pm.read_short(address)
        except Exception as e:
            logger.debug(f"read_short hatası (0x{address:X}): {e}")
            return None
    
    def read_long(self, address: int) -> Optional[int]:
        """
        Bellekten long (4 byte) okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[int]: Okunan değer veya hata durumunda None
        """
        try:
            return self.pm.read_long(address)
        except Exception as e:
            logger.debug(f"read_long hatası (0x{address:X}): {e}")
            return None
    
    def read_bytes(self, address: int, size: int) -> Optional[bytes]:
        """
        Bellekten byte dizisi okur
        
        Args:
            address: Okunacak adres
            size: Okunacak byte sayısı
            
        Returns:
            Optional[bytes]: Okunan byte dizisi veya hata durumunda None
        """
        try:
            return self.pm.read_bytes(address, size)
        except Exception as e:
            logger.debug(f"read_bytes hatası (0x{address:X}): {e}")
            return None
    
    def read_string(self, address: int, max_length: int = 64) -> Optional[str]:
        """
        Bellekten string okur
        
        Args:
            address: Okunacak adres
            max_length: Maksimum string uzunluğu
            
        Returns:
            Optional[str]: Okunan string veya hata durumunda None
        """
        try:
            return self.pm.read_string(address, max_length)
        except Exception as e:
            logger.debug(f"read_string hatası (0x{address:X}): {e}")
            return None
    
    def read_vector3(self, address: int) -> Optional[tuple]:
        """
        Bellekten 3D vektör (x, y, z) okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[tuple]: (x, y, z) tuple veya hata durumunda None
        """
        try:
            data = self.read_bytes(address, 12)  # 3 * 4 bytes
            if data:
                x, y, z = struct.unpack('fff', data)
                return (x, y, z)
        except Exception as e:
            logger.debug(f"read_vector3 hatası (0x{address:X}): {e}")
        return None
    
    def read_matrix_4x4(self, address: int) -> Optional[list]:
        """
        Bellekten 4x4 matris okur
        
        Args:
            address: Okunacak adres
            
        Returns:
            Optional[list]: 4x4 matris (16 float) veya hata durumunda None
        """
        try:
            data = self.read_bytes(address, 64)  # 16 * 4 bytes
            if data:
                matrix = struct.unpack('ffff' * 4, data)
                return [list(matrix[i:i+4]) for i in range(0, 16, 4)]
        except Exception as e:
            logger.debug(f"read_matrix_4x4 hatası (0x{address:X}): {e}")
        return None
    
    def write_int(self, address: int, value: int) -> bool:
        """
        Belleğe integer yazar
        
        Args:
            address: Yazılacak adres
            value: Yazılacak değer
            
        Returns:
            bool: Yazma başarılı ise True
        """
        try:
            self.pm.write_int(address, value)
            return True
        except Exception as e:
            logger.error(f"write_int hatası (0x{address:X}): {e}")
            return False
    
    def write_float(self, address: int, value: float) -> bool:
        """
        Belleğe float yazar
        
        Args:
            address: Yazılacak adres
            value: Yazılacak değer
            
        Returns:
            bool: Yazma başarılı ise True
        """
        try:
            self.pm.write_float(address, value)
            return True
        except Exception as e:
            logger.error(f"write_float hatası (0x{address:X}): {e}")
            return False
    
    def write_bytes(self, address: int, value: bytes) -> bool:
        """
        Belleğe byte dizisi yazar
        
        Args:
            address: Yazılacak adres
            value: Yazılacak byte dizisi
            
        Returns:
            bool: Yazma başarılı ise True
        """
        try:
            self.pm.write_bytes(address, value)
            return True
        except Exception as e:
            logger.error(f"write_bytes hatası (0x{address:X}): {e}")
            return False
    
    def get_module_base(self, module_name: str) -> Optional[int]:
        """
        Modül base adresini döndürür
        
        Args:
            module_name: Modül adı (örn: "client.dll")
            
        Returns:
            Optional[int]: Modül base adresi veya None
        """
        try:
            module = pymem.process.module_from_name(
                self.pm.process_handle, module_name
            )
            return module.lpBaseOfDll if module else None
        except Exception as e:
            logger.error(f"Modül base adresi alınamadı ({module_name}): {e}")
            return None
    
    def close(self):
        """Bellek okuyucuyu kapatır"""
        if self.pm:
            self.pm.close_process()
        self.is_connected = False
        logger.info("Bellek okuyucu kapatıldı")
