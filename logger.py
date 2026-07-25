"""
Logging Modülü
Uygulama loglarını yönetir
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os

def setup_logger(name: str, log_file: str = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Logger oluşturur ve yapılandırır
    
    Args:
        name: Logger adı
        log_file: Log dosyası yolu (opsiyonel)
        level: Log seviyesi
        
    Returns:
        logging.Logger: Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Eğer zaten handler varsa tekrar ekleme
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (opsiyonel)
    if log_file:
        # Log dizinini oluştur
        log_dir = Path(log_file).parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Mevcut logger'ı döndürür veya yeni oluşturur
    
    Args:
        name: Logger adı
        
    Returns:
        logging.Logger: Logger
    """
    return logging.getLogger(name)

class Logger:
    """
    Logger wrapper sınıfı
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.log_dir = "logs"
        self.current_log_file = None
        self._init_log_dir()
    
    def _init_log_dir(self):
        """Log dizinini oluşturur"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def get_log_file(self) -> str:
        """
        Günün log dosyasını döndürür
        
        Returns:
            str: Log dosyası yolu
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"fps_mechanics_{today}.log")
        return log_file
    
    def get_logger(self, name: str, level: int = logging.DEBUG) -> logging.Logger:
        """
        Logger oluşturur veya mevcut olanı döndürür
        
        Args:
            name: Logger adı
            level: Log seviyesi
            
        Returns:
            logging.Logger: Logger
        """
        if name not in self._loggers:
            log_file = self.get_log_file()
            self._loggers[name] = setup_logger(name, log_file, level)
        return self._loggers[name]
    
    def set_level(self, name: str, level: int):
        """
        Logger seviyesini değiştirir
        
        Args:
            name: Logger adı
            level: Yeni seviye
        """
        if name in self._loggers:
            self._loggers[name].setLevel(level)
    
    def close(self):
        """Tüm logger'ları kapatır"""
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)
        self._loggers.clear()
