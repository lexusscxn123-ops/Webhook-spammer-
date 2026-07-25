"""
Radar (Minimap) Modülü
Oyuncuları ve nesneleri gösteren 2D radar
"""

import sys
import json
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QCheckBox
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from typing import Dict, List, Optional
import os

from ..core.entity_manager import EntityManager, Entity
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class RadarWindow(QWidget):
    """
    PyQt5 tabanlı radar (minimap) penceresi
    """
    
    def __init__(self, entity_manager: EntityManager, map_name: str = "de_dust2",
                 width: int = 400, height: int = 400):
        """
        RadarWindow başlatıcısı
        
        Args:
            entity_manager: EntityManager nesnesi
            map_name: Harita adı
            width: Radar genişliği
            height: Radar yüksekliği
        """
        super().__init__()
        
        self.entity_manager = entity_manager
        self.map_name = map_name
        self.width = width
        self.height = height
        
        # Radar ayarları
        self.zoom_level = 1.0
        self.show_names = True
        self.show_bomb = True
        
        # Harita verilerini yükle
        self.map_data = self.load_map_data(map_name)
        
        # UI ayarları
        self.setup_ui()
        
        # Güncelleme timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(50)  # 20 FPS
        
        logger.info(f"Radar başlatıldı: {map_name}")
    
    def load_map_data(self, map_name: str) -> Dict:
        """
        Harita verilerini JSON dosyasından yükler
        
        Args:
            map_name: Harita adı
            
        Returns:
            Dict: Harita verileri
        """
        map_config_path = os.path.join(
            os.path.dirname(__file__), 
            'map_configs', 
            f'{map_name}.json'
        )
        
        default_map_data = {
            'world_size': [3000, 3000],
            'center': [0, 0],
            'scale': 1.0,
            'rotation': 0,
            'image': None,
            'grid_size': 500
        }
        
        try:
            if os.path.exists(map_config_path):
                with open(map_config_path, 'r') as f:
                    map_data = json.load(f)
                    logger.info(f"Harita verileri yüklendi: {map_name}")
                    return map_data
            else:
                logger.warning(f"Harita konfigürasyonu bulunamadı: {map_name}, varsayılan kullanılıyor")
                return default_map_data
        except Exception as e:
            logger.error(f"Harita verileri yüklenirken hata: {e}")
            return default_map_data
    
    def setup_ui(self):
        """UI ayarlarını yapar"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle(f"Radar - {self.map_name}")
        self.setGeometry(100, 100, self.width, self.height + 50)
        self.setMinimumSize(300, 300)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Radar canvas
        self.canvas = QWidget()
        self.canvas.setMinimumSize(self.width, self.height)
        self.canvas.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        layout.addWidget(self.canvas)
        
        # Kontroller
        control_layout = QVBoxLayout()
        
        # Zoom slider
        zoom_layout = QVBoxLayout()
        zoom_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        control_layout.addLayout(zoom_layout)
        
        # Options
        options_layout = QVBoxLayout()
        self.name_checkbox = QCheckBox("Show Names")
        self.name_checkbox.setChecked(True)
        self.name_checkbox.toggled.connect(self.on_show_names_toggled)
        options_layout.addWidget(self.name_checkbox)
        
        self.bomb_checkbox = QCheckBox("Show Bomb")
        self.bomb_checkbox.setChecked(True)
        self.bomb_checkbox.toggled.connect(self.on_show_bomb_toggled)
        options_layout.addWidget(self.bomb_checkbox)
        
        control_layout.addLayout(options_layout)
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def on_zoom_changed(self, value: int):
        """Zoom değiştiğinde çağrılır"""
        self.zoom_level = value / 100.0
    
    def on_show_names_toggled(self, checked: bool):
        """İsim gösterimi değiştiğinde çağrılır"""
        self.show_names = checked
    
    def on_show_bomb_toggled(self, checked: bool):
        """Bomba gösterimi değiştiğinde çağrılır"""
        self.show_bomb = checked
    
    def paintEvent(self, event):
        """
        Paint event - Radar çizimleri
        """
        # Canvas üzerine çiz
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Arka plan
        painter.fillRect(0, 0, self.canvas.width(), self.canvas.height(), 
                        QColor(0, 0, 0, 200))
        
        # Harita boyutları
        map_width = self.map_data['world_size'][0]
        map_height = self.map_data['world_size'][1]
        map_center = self.map_data['center']
        
        # Local player
        local_player = self.entity_manager.local_player
        if not local_player or not local_player.is_alive:
            painter.end()
            return
        
        local_pos = local_player.position
        
        # Dünya koordinatlarını radar koordinatlarına dönüştür
        def world_to_radar(world_pos):
            # Merkezileştir
            dx = world_pos[0] - local_pos[0]
            dz = world_pos[2] - local_pos[2]  # Z ekseni radar için Y olarak kullanılır
            
            # Ölçekle
            scale = 20.0 * self.zoom_level
            rx = dx * scale + self.canvas.width() / 2
            ry = -dz * scale + self.canvas.height() / 2
            
            # Local player rotasyonu (Y ekseni etrafında)
            angle = local_player.view_angles[0]  # Yaw
            rotated_x = rx * np.cos(angle) - ry * np.sin(angle)
            rotated_y = rx * np.sin(angle) + ry * np.cos(angle)
            
            return QPointF(rotated_x, rotated_y)
        
        # Grid çiz
        self.draw_grid(painter, local_pos)
        
        # Takım arkadaşları
        team_mates = self.entity_manager.get_team_mates(local_player.team)
        for mate in team_mates:
            if mate.is_alive:
                pos = world_to_radar(mate.position)
                self.draw_player(painter, pos, mate, QColor(0, 255, 0), is_local=False)
        
        # Düşmanlar
        enemies = self.entity_manager.get_enemies(local_player.team)
        for enemy in enemies:
            if enemy.is_alive:
                pos = world_to_radar(enemy.position)
                self.draw_player(painter, pos, enemy, QColor(255, 0, 0), is_local=False)
        
        # Local player
        center = QPointF(self.canvas.width() / 2, self.canvas.height() / 2)
        self.draw_player(painter, center, local_player, QColor(0, 255, 255), is_local=True)
        
        painter.end()
    
    def draw_grid(self, painter: QPainter, center_pos: np.ndarray):
        """
        Radar grid'ini çizer
        
        Args:
            painter: QPainter nesnesi
            center_pos: Radar merkez pozisyonu
        """
        grid_size = self.map_data.get('grid_size', 500)
        scale = 20.0 * self.zoom_level
        
        painter.setPen(QPen(QColor(100, 100, 100, 50), 1, Qt.DashLine))
        
        # X ekseni grid çizgileri
        grid_center_x = int(self.canvas.width() / 2)
        grid_center_y = int(self.canvas.height() / 2)
        
        # Grid çizgilerini dünya koordinatlarına göre hesapla
        offset_x = int(center_pos[0] % grid_size)
        offset_z = int(center_pos[2] % grid_size)
        
        for i in range(-5, 6):
            # X ekseni
            x = grid_center_x + int(i * grid_size * scale) - offset_x
            painter.drawLine(int(x), 0, int(x), self.canvas.height())
            
            # Z ekseni (Y olarak göster)
            y = grid_center_y + int(i * grid_size * scale) + offset_z
            painter.drawLine(0, int(y), self.canvas.width(), int(y))
    
    def draw_player(self, painter: QPainter, pos: QPointF, entity: Entity,
                   color: QColor, is_local: bool = False):
        """
        Oyuncu ikonu çizer
        
        Args:
            painter: QPainter nesnesi
            pos: Radar pozisyonu
            entity: Entity nesnesi
            color: Renk
            is_local: Yerel oyuncu mu?
        """
        # Boyut
        size = 8 if is_local else 6
        
        # Kare veya üçgen çiz
        if is_local:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 1))
            painter.drawRect(QRectF(pos.x() - size, pos.y() - size, size * 2, size * 2))
        else:
            # Bakış yönüne göre üçgen çiz
            angle = entity.view_angles[0]  # Yaw
            points = [
                QPointF(pos.x() + size * np.cos(angle), pos.y() - size * np.sin(angle)),
                QPointF(pos.x() + size * np.cos(angle + 2.5), pos.y() - size * np.sin(angle + 2.5)),
                QPointF(pos.x() + size * np.cos(angle - 2.5), pos.y() - size * np.sin(angle - 2.5))
            ]
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 1))
            painter.drawPolygon(QPolygonF(points))
        
        # İsim
        if self.show_names and not is_local:
            painter.setPen(QPen(Qt.white, 1))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(int(pos.x() - 20), int(pos.y() - 15), "Player")
        
        # Sağlık
        if not is_local:
            health_text = f"{entity.health}"
            painter.setPen(QPen(Qt.green if entity.health > 50 else Qt.red, 1))
            painter.setFont(QFont('Arial', 7))
            painter.drawText(int(pos.x() - 10), int(pos.y() + 15), health_text)
    
    def update_display(self):
        """
        Ekranı günceller
        """
        self.canvas.update()
