import logging

logger = logging.getLogger(__name__)

class SignatureScanner:
    def __init__(self):
        self.last_result = 0
    
    def scan(self, memory_reader, module_name: str, signature: str, offset: int = 0):
        return None
