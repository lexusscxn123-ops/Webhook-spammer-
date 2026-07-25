"""
PyQt5 Overlay Modülü
ESP görüntüleme için şeffaf overlay penceresi
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygon
from typing import List, Optional
import logging

from ..core.entity_manager import Entity, EntityManager
from ..math.w2s import world_to_screen_numba
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ESPOverlay(QWidget):
    """
    PyQt5 tabanlı ESP overlay penceresi
    """
    
    def __init__(self, entity_manager: EntityManager, view_matrix_getter, 
                 screen_width: int = 1920, screen_height: int = 1080):
        """
        ESPOverlay başlatıcısı
        
        Args:
            entity_manager: EntityManager nesnesi
            view_matrix_getter: View matrix döndüren fonksiyon
            screen_width: Ekran genişliği
            screen_height: Ekran yüksekliği
        """
        super().__init__()
        
        self.entity_manager = entity_manager
        self.view_matrix_getter = view_matrix_getter
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # ESP ayarları
        self.settings = {
            'box_enabled': True,
            'skeleton_enabled': True,
            'healthbar_enabled': True,
            'name_enabled': True,
            'distance_enabled': True,
            'snapline_enabled': False,
            'head_circle_enabled': True,
            'visibility_check': True,
            'team_colors': {
                't': QColor(255, 100, 100),
                'ct': QColor(100, 100, 255),
                'spectator': QColor(255, 255, 0)
            }
        }
        
        self.setup_ui()
        
        # Güncelleme timer'ı
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(16)  # ~60 FPS
        
        logger.info("PyQt5 ESP overlay başlatıldı")
    
    def setup_ui(self):
        """UI ayarlarını yapar"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.showFullScreen()
        
        logger.info(f"ESP overlay boyutu: {self.screen_width}x{self.screen_height}")
    
    def paintEvent(self, event):
        """
        Paint event - ESP çizimleri burada yapılır
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # View matrix'i al
        view_matrix = self.view_matrix_getter()
        if view_matrix is None:
            painter.end()
            return
        
        # Local player'ı al
        local_player = self.entity_manager.local_player
        if not local_player or not local_player.is_alive:
            painter.end()
            return
        
        # Düşman ve takım arkadaşlarını al
        enemies = self.entity_manager.get_enemies(local_player.team)
        team_mates = self.entity_manager.get_team_mates(local_player.team)
        
        # Tüm entity'leri çiz
        for entity in enemies:
            self.draw_entity(painter, entity, view_matrix, local_player, is_enemy=True)
        
        for entity in team_mates:
            self.draw_entity(painter, entity, view_matrix, local_player, is_enemy=False)
        
        painter.end()
    
    def draw_entity(self, painter: QPainter, entity: Entity, view_matrix: np.ndarray,
                    local_player: Entity, is_enemy: bool = True):
        """
        Tek bir entity'yi çizer
        
        Args:
            painter: QPainter nesnesi
            entity: Çizilecek entity
            view_matrix: View matrix
            local_player: Yerel oyuncu
            is_enemy: Düşman mı?
        """
        # Entity ekranda mı kontrol et
        screen_pos = world_to_screen_numba(entity.position, view_matrix, 
                                          self.screen_width, self.screen_height)
        if screen_pos is None:
            return
        
        # Görünürlük kontrolü
        if self.settings['visibility_check']:
            visible = entity.is_visible(local_player.position, 
                                       local_player.view_angles, view_matrix)
        else:
            visible = True
        
        # Renk seçimi
        team = entity.team
        if team == 3:  # T
            color = self.settings['team_colors']['t']
        elif team == 2:  # CT
            color = self.settings['team_colors']['ct']
        else:
            color = self.settings['team_colors']['spectator']
        
        # Görünürlük durumuna göre renk ayarı
        if not visible:
            color = QColor(color.red() // 2, color.green() // 2, color.blue() // 2)
        
        # ESP çizimleri
        if self.settings['box_enabled']:
            self.draw_box(painter, entity, screen_pos, color)
        
        if self.settings['skeleton_enabled']:
            self.draw_skeleton(painter, entity, view_matrix, color)
        
        if self.settings['healthbar_enabled']:
            self.draw_healthbar(painter, entity, screen_pos)
        
        if self.settings['name_enabled']:
            self.draw_name(painter, entity, screen_pos, color)
        
        if self.settings['distance_enabled']:
            self.draw_distance(painter, entity, local_player, screen_pos, color)
        
        if self.settings['snapline_enabled']:
            self.draw_snapline(painter, entity, screen_pos, color)
        
        if self.settings['head_circle_enabled']:
            self.draw_head_circle(painter, entity, view_matrix, color)
    
    def draw_box(self, painter: QPainter, entity: Entity, 
                 screen_pos: tuple, color: QColor):
        """
        Box ESP çizer
        """
        # Basit box boyutları (oyuncu boyutuna göre)
        distance = entity.distance_to(self.entity_manager.local_player.position)
        box_size = max(30, 800 / max(distance, 1))  # Uzaklığa göre boyutlandır
        
        x, y = screen_pos
        half_size = box_size / 2
        
        # Box çiz
        painter.setPen(QPen(color, 2))
        painter.drawRect(int(x - half_size), int(y - box_size), 
                        int(box_size), int(box_size * 1.5))
    
    def draw_skeleton(self, painter: QPainter, entity: Entity, 
                     view_matrix: np.ndarray, color: QColor):
        """
        Skeleton (iskelet) ESP çizer
        """
        bones = entity.bone_positions
        if not bones:
            return
        
        # Kemik pozisyonlarını ekrana dönüştür
        bone_screens = {}
        for name, pos in bones.items():
            screen = world_to_screen_numba(pos, view_matrix,
                                          self.screen_width, self.screen_height)
            if screen:
                bone_screens[name] = screen
        
        # Kemikleri birleştir
        painter.setPen(QPen(color, 2, Qt.SolidLine))
        
        # Önemli kemik bağlantıları
        connections = [
            ('head', 'neck'),
            ('neck', 'chest'),
            ('chest', 'stomach'),
            ('stomach', 'pelvis'),
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_foot'),
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_foot')
        ]
        
        for bone1, bone2 in connections:
            if bone1 in bone_screens and bone2 in bone_screens:
                p1 = bone_screens[bone1]
                p2 = bone_screens[bone2]
                painter.drawLine(int(p1[0]), int(p1[1]), 
                               int(p2[0]), int(p2[1]))
    
    def draw_healthbar(self, painter: QPainter, entity: Entity, 
                      screen_pos: tuple):
        """
        Sağlık barı çizer
        """
        x, y = screen_pos
        health = entity.health
        max_health = 100
        
        # Bar boyutları
        bar_width = 6
        bar_height = 80
        bar_x = int(x + 20)
        bar_y = int(y - 40)
        
        # Arka plan
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.black))
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
        
        # Sağlık
        health_ratio = health / max_health
        health_height = int(bar_height * health_ratio)
        
        # Renk (kırmızıdan yeşile)
        if health_ratio > 0.6:
            color = QColor(0, 255, 0)
        elif health_ratio > 0.3:
            color = QColor(255, 255, 0)
        else:
            color = QColor(255, 0, 0)
        
        painter.setBrush(QBrush(color))
        painter.drawRect(bar_x, bar_y + bar_height - health_height, 
                        bar_width, health_height)
        
        # Sağlık değeri
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont('Arial', 8))
        painter.drawText(bar_x - 10, bar_y - 5, f"{health}")
    
    def draw_name(self, painter: QPainter, entity: Entity, 
                 screen_pos: tuple, color: QColor):
        """
        Oyuncu ismi çizer
        """
        x, y = screen_pos
        # Basit isim (gerçek isim okuma implementasyonu yapılabilir)
        name = f"Player_{entity.address & 0xFF}"
        
        painter.setPen(QPen(color, 1))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(int(x - 30), int(y - 70), name)
    
    def draw_distance(self, painter: QPainter, entity: Entity,
                     local_player: Entity, screen_pos: tuple, color: QColor):
        """
        Mesafe bilgisi çizer
        """
        x, y = screen_pos
        distance = entity.distance_to(local_player.position)
        
        painter.setPen(QPen(color, 1))
        painter.setFont(QFont('Arial', 9))
        painter.drawText(int(x - 15), int(y + 20), f"{distance:.1f}m")
    
    def draw_snapline(self, painter: QPainter, entity: Entity,
                     screen_pos: tuple, color: QColor):
        """
        Snapline (hedef çizgisi) çizer
        """
        x, y = screen_pos
        painter.setPen(QPen(color, 1, Qt.DashLine))
        painter.drawLine(int(self.screen_width / 2), self.screen_height,
                        int(x), int(y))
    
    def draw_head_circle(self, painter: QPainter, entity: Entity,
                        view_matrix: np.ndarray, color: QColor):
        """
        Kafa çemberi çizer
        """
        head_pos = entity.bone_positions.get('head')
        if head_pos is not None:
            screen_pos = world_to_screen_numba(head_pos, view_matrix,
                                              self.screen_width, self.screen_height)
            if screen_pos:
                # Kafa boyutunu tahmin et
                distance = entity.distance_to(self.entity_manager.local_player.position)
                head_size = max(3, 20 / max(distance / 10, 1))
                
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
                painter.drawEllipse(int(screen_pos[0] - head_size),
                                  int(screen_pos[1] - head_size),
                                  int(head_size * 2), int(head_size * 2))
    
    def update_display(self):
        """
        Ekranı günceller
        """
        self.update()  # QWidget.update() çağırır
    
    def closeEvent(self, event):
        """
        Pencere kapatıldığında çağrılır
        """
        self.timer.stop()
        logger.info("ESP overlay kapatıldı")
        event.accept()
