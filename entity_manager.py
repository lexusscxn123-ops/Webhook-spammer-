"""
Entity Manager Modülü
CS2 oyun entity'lerini yönetir
"""

from typing import List, Dict, Optional
import numpy as np
from ..core.memory_reader import MemoryReader
from ..utils.logger import setup_logger
import json
import os

logger = setup_logger(__name__)

class Entity:
    """
    CS2 oyun entity sınıfı
    Bir oyuncu veya nesneyi temsil eder
    """
    
    def __init__(self, address: int, memory_reader: MemoryReader, offsets: Dict):
        """
        Entity başlatıcısı
        
        Args:
            address: Entity bellek adresi
            memory_reader: MemoryReader nesnesi
            offsets: Offset sözlüğü
        """
        self.address = address
        self.memory = memory_reader
        self.offsets = offsets
        self._cache = {}
        
    @property
    def health(self) -> int:
        """Sağlık değeri"""
        if 'health' not in self._cache:
            offset = self.offsets.get('m_iHealth', 0)
            self._cache['health'] = self.memory.read_int(self.address + offset) or 0
        return self._cache['health']
    
    @property
    def team(self) -> int:
        """Takım numarası (2=CT, 3=T, 1=spectator)"""
        if 'team' not in self._cache:
            offset = self.offsets.get('m_iTeamNum', 0)
            self._cache['team'] = self.memory.read_int(self.address + offset) or 0
        return self._cache['team']
    
    @property
    def position(self) -> np.ndarray:
        """Dünya koordinatları (x, y, z)"""
        if 'position' not in self._cache:
            offset = self.offsets.get('m_vecOrigin', 0)
            pos = self.memory.read_vector3(self.address + offset)
            self._cache['position'] = np.array(pos) if pos else np.zeros(3)
        return self._cache['position']
    
    @property
    def view_angles(self) -> np.ndarray:
        """Bakış açısı (yaw, pitch)"""
        if 'view_angles' not in self._cache:
            offset = self.offsets.get('m_angEyeAngles', 0)
            angles = self.memory.read_vector3(self.address + offset)
            self._cache['view_angles'] = np.array(angles[:2]) if angles else np.zeros(2)
        return self._cache['view_angles']
    
    @property
    def is_alive(self) -> bool:
        """Entity canlı mı?"""
        if 'is_alive' not in self._cache:
            life_state = self.memory.read_int(
                self.address + self.offsets.get('m_lifeState', 0)
            ) or 0
            self._cache['is_alive'] = life_state == 0 and self.health > 0
        return self._cache['is_alive']
    
    @property
    def is_dormant(self) -> bool:
        """Entity dormant (uyku) durumunda mı?"""
        if 'is_dormant' not in self._cache:
            offset = self.offsets.get('m_bDormant', 0)
            self._cache['is_dormant'] = bool(
                self.memory.read_int(self.address + offset) or 0
            )
        return self._cache['is_dormant']
    
    @property
    def is_flashed(self) -> bool:
        """Entity flashlanmış mı?"""
        if 'is_flashed' not in self._cache:
            offset = self.offsets.get('m_flFlashDuration', 0)
            flash_duration = self.memory.read_float(self.address + offset) or 0
            self._cache['is_flashed'] = flash_duration > 0.1
        return self._cache['is_flashed']
    
    @property
    def is_scoped(self) -> bool:
        """Entity scope (nişangah) kullanıyor mu?"""
        if 'is_scoped' not in self._cache:
            offset = self.offsets.get('m_bIsScoped', 0)
            self._cache['is_scoped'] = bool(
                self.memory.read_int(self.address + offset) or 0
            )
        return self._cache['is_scoped']
    
    @property
    def bone_matrix(self) -> Optional[np.ndarray]:
        """Kemik matrisi (skeleton için)"""
        if 'bone_matrix' not in self._cache:
            offset = self.offsets.get('m_pBoneMatrix', 0)
            matrix_addr = self.memory.read_long(self.address + offset)
            if matrix_addr:
                # Bone matrix'i oku (128 kemik için 128 * 4x4 = 2048 byte)
                bone_data = self.memory.read_bytes(matrix_addr, 2048)
                if bone_data:
                    self._cache['bone_matrix'] = np.frombuffer(
                        bone_data, dtype=np.float32
                    ).reshape(128, 4, 4)
        return self._cache['bone_matrix']
    
    @property
    def bone_positions(self) -> Dict[str, np.ndarray]:
        """Önemli kemik pozisyonları"""
        if 'bone_positions' not in self._cache and self.bone_matrix is not None:
            bones = {}
            # Önemli kemik indeksleri (CS2 için)
            bone_indices = {
                'head': 6,
                'neck': 5,
                'chest': 4,
                'stomach': 2,
                'pelvis': 0,
                'left_shoulder': 8,
                'right_shoulder': 13,
                'left_elbow': 9,
                'right_elbow': 14,
                'left_wrist': 10,
                'right_wrist': 15,
                'left_hip': 1,
                'right_hip': 16,
                'left_knee': 3,
                'right_knee': 18,
                'left_foot': 7,
                'right_foot': 22
            }
            
            matrix = self.bone_matrix
            for name, idx in bone_indices.items():
                if idx < len(matrix):
                    # Pozisyonu matristen çıkar
                    pos = matrix[idx][:3, 3]
                    bones[name] = np.array([pos[0], pos[1], pos[2]])
            
            self._cache['bone_positions'] = bones
        return self._cache.get('bone_positions', {})
    
    def distance_to(self, other_position: np.ndarray) -> float:
        """
        Başka bir pozisyona olan mesafeyi hesaplar
        
        Args:
            other_position: Diğer pozisyon
            
        Returns:
            float: Mesafe (metre cinsinden)
        """
        return float(np.linalg.norm(self.position - other_position))
    
    def is_visible(self, local_player_position: np.ndarray, 
                   local_player_angles: np.ndarray, 
                   view_matrix: np.ndarray) -> bool:
        """
        Entity görünür mü? (Basit raycasting ile)
        
        Args:
            local_player_position: Yerel oyuncu pozisyonu
            local_player_angles: Yerel oyuncu bakış açısı
            view_matrix: View matrix
            
        Returns:
            bool: Entity görünür ise True
        """
        # Basit görünürlük kontrolü
        # İleriye doğru ışın atarak engel var mı kontrol et
        # Bu basit bir implementasyon, tam doğruluk için daha gelişmiş yöntemler gerekli
        
        from ..math.w2s import world_to_screen
        
        screen_pos = world_to_screen(self.position, view_matrix)
        if screen_pos is None:
            return False
            
        # Ekran merkezine olan mesafeyi kontrol et
        center = np.array([960, 540])  # 1920x1080 için
        distance_to_center = np.linalg.norm(screen_pos - center)
        
        # Eğer ekran merkezine yakınsa görünür olabilir
        return distance_to_center < 500  # Piksel cinsinden
    def clear_cache(self):
        """Cache'i temizler"""
        self._cache.clear()
        logger.debug(f"Entity {hex(self.address)} cache'i temizlendi")

class EntityManager:
    """
    CS2 entity yöneticisi
    Tüm entity'leri listeler ve yönetir
    """
    
    def __init__(self, memory_reader: MemoryReader, offsets: Dict):
        """
        EntityManager başlatıcısı
        
        Args:
            memory_reader: MemoryReader nesnesi
            offsets: Offset sözlüğü
        """
        self.memory = memory_reader
        self.offsets = offsets
        self.entities: List[Entity] = []
        self.local_player: Optional[Entity] = None
        
    def update(self) -> int:
        """
        Tüm entity'leri günceller
        
        Returns:
            int: Güncellenen entity sayısı
        """
        self.entities = []
        self.local_player = None
        
        # Local player'ı al
        local_pawn_addr = self.memory.read_int(
            self.memory.module_base + self.offsets.get('dwLocalPlayerPawn', 0)
        )
        
        if local_pawn_addr:
            self.local_player = Entity(local_pawn_addr, self.memory, self.offsets)
        
        # Entity listesini al
        entity_list_addr = self.memory.read_int(
            self.memory.module_base + self.offsets.get('dwEntityList', 0)
        )
        
        if not entity_list_addr:
            logger.warning("Entity listesi bulunamadı!")
            return 0
        
        # Entity listesini tara (max 64 oyuncu)
        for i in range(64):
            # Her entity için list offset'ini hesapla
            list_entry = self.memory.read_int(entity_list_addr + (i * 0x8))
            if not list_entry:
                continue
                
            entity_addr = self.memory.read_int(list_entry + 0x0)
            if not entity_addr:
                continue
            
            # Controller'dan pawn adresini al
            pawn_addr = self.memory.read_int(entity_addr + self.offsets.get('m_hPlayerPawn', 0))
            if not pawn_addr:
                continue
            
            entity = Entity(pawn_addr, self.memory, self.offsets)
            
            # Sadece canlı ve aktif entity'leri ekle
            if entity.is_alive and not entity.is_dormant:
                self.entities.append(entity)
        
        logger.debug(f"Toplam {len(self.entities)} entity güncellendi")
        return len(self.entities)
    
    def get_enemies(self, local_team: int = None) -> List[Entity]:
        """
        Düşman entity'lerini döndürür
        
        Args:
            local_team: Yerel oyuncu takımı (belirtilmezse otomatik alınır)
            
        Returns:
            List[Entity]: Düşman entity listesi
        """
        if local_team is None and self.local_player:
            local_team = self.local_player.team
            
        return [e for e in self.entities if e.team != local_team]
    
    def get_team_mates(self, local_team: int = None) -> List[Entity]:
        """
        Takım arkadaşlarını döndürür
        
        Args:
            local_team: Yerel oyuncu takımı (belirtilmezse otomatik alınır)
            
        Returns:
            List[Entity]: Takım arkadaşı listesi
        """
        if local_team is None and self.local_player:
            local_team = self.local_player.team
            
        return [e for e in self.entities if e.team == local_team and e != self.local_player]
    
    def get_entity_by_index(self, index: int) -> Optional[Entity]:
        """
        Index'e göre entity döndürür
        
        Args:
            index: Entity index
            
        Returns:
            Optional[Entity]: Entity veya None
        """
        if 0 <= index < len(self.entities):
            return self.entities[index]
        return None
    
    def clear_cache(self):
        """Tüm entity cache'lerini temizler"""
        for entity in self.entities:
            entity.clear_cache()
        if self.local_player:
            self.local_player.clear_cache()
        logger.debug("Tüm entity cache'leri temizlendi")
