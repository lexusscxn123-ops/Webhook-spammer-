import json
import logging

logger = logging.getLogger(__name__)

class OffsetManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.offsets = {}
        self.entity_offsets = {}
        self.load_offsets()
    
    def load_offsets(self) -> bool:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.offsets = config.get('offsets', {})
                self.entity_offsets = config.get('entity_offsets', {})
                return True
        except Exception as e:
            logger.error(f"Offset yükleme hatası: {e}")
            return False
    
    def get_offset(self, name: str) -> int:
        return self.offsets.get(name, 0)
    
    def get_entity_offset(self, name: str) -> int:
        return self.entity_offsets.get(name, 0)
    
    def get_all_offsets(self) -> dict:
        return {**self.offsets, **self.entity_offsets}
    
    def update_offsets(self, memory_reader, signature_scanner) -> bool:
        return True
