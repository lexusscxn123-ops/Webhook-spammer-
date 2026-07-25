"""
World to Screen (W2S) Matematik Modülü
3D dünya koordinatlarını 2D ekran koordinatlarına dönüştürür
"""

import numpy as np
from numba import jit, njit
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

@njit(cache=True)
def world_to_screen_numba(world_pos: np.ndarray, view_matrix: np.ndarray, 
                         screen_width: int = 1920, screen_height: int = 1080) -> Optional[Tuple[float, float]]:
    """
    Numba ile hızlandırılmış World to Screen dönüşümü
    
    Args:
        world_pos: 3D dünya pozisyonu (x, y, z)
        view_matrix: 4x4 view matrisi
        screen_width: Ekran genişliği
        screen_height: Ekran yüksekliği
        
    Returns:
        Optional[Tuple[float, float]]: (x, y) ekran koordinatları veya None
    """
    # 4x4 matris ile çarpma için 4D vektöre dönüştür
    vec4 = np.array([
        world_pos[0] * view_matrix[0][0] + world_pos[1] * view_matrix[0][1] + world_pos[2] * view_matrix[0][2] + view_matrix[0][3],
        world_pos[0] * view_matrix[1][0] + world_pos[1] * view_matrix[1][1] + world_pos[2] * view_matrix[1][2] + view_matrix[1][3],
        world_pos[0] * view_matrix[2][0] + world_pos[1] * view_matrix[2][1] + world_pos[2] * view_matrix[2][2] + view_matrix[2][3],
        world_pos[0] * view_matrix[3][0] + world_pos[1] * view_matrix[3][1] + world_pos[2] * view_matrix[3][2] + view_matrix[3][3]
    ])
    
    # Perspektif bölme (clip space -> NDC)
    if vec4[3] < 0.001:
        return None
    
    ndc_x = vec4[0] / vec4[3]
    ndc_y = vec4[1] / vec4[3]
    
    # NDC -> Screen space
    screen_x = (screen_width / 2) * (ndc_x + 1)
    screen_y = (screen_height / 2) * (1 - ndc_y)  # Y ekseni ters
    
    # Ekran sınırları içinde mi kontrol et
    if screen_x < 0 or screen_x > screen_width or screen_y < 0 or screen_y > screen_height:
        return None
    
    return (screen_x, screen_y)

def world_to_screen(world_pos: np.ndarray, view_matrix: np.ndarray, 
                   screen_width: int = 1920, screen_height: int = 1080) -> Optional[Tuple[float, float]]:
    """
    World to Screen dönüşümü (Python versiyonu - eğitim amaçlı)
    
    3D dünya koordinatlarını 2D ekran koordinatlarına dönüştürür.
    Dönüşüm adımları:
    1. World space -> Clip space (View Matrix ile)
    2. Clip space -> NDC (Normalized Device Coordinates)
    3. NDC -> Screen space
    
    View Matrix yapısı (4x4):
    [row0]: X ekseni (right)
    [row1]: Y ekseni (up)
    [row2]: Z ekseni (forward)
    [row3]: Translation (position)
    
    Args:
        world_pos: 3D dünya pozisyonu (x, y, z)
        view_matrix: 4x4 view matrisi
        screen_width: Ekran genişliği
        screen_height: Ekran yüksekliği
        
    Returns:
        Optional[Tuple[float, float]]: (x, y) ekran koordinatları veya None
    """
    # View matrix'in boyutunu kontrol et
    if len(view_matrix) != 4 or len(view_matrix[0]) != 4:
        logger.error("Geçersiz view matrix boyutu!")
        return None
    
    # World space -> Clip space
    # 4x4 matris ile çarpma için 4D vektör kullan
    vec4 = np.array([
        world_pos[0] * view_matrix[0][0] + world_pos[1] * view_matrix[0][1] + world_pos[2] * view_matrix[0][2] + view_matrix[0][3],
        world_pos[0] * view_matrix[1][0] + world_pos[1] * view_matrix[1][1] + world_pos[2] * view_matrix[1][2] + view_matrix[1][3],
        world_pos[0] * view_matrix[2][0] + world_pos[1] * view_matrix[2][1] + world_pos[2] * view_matrix[2][2] + view_matrix[2][3],
        world_pos[0] * view_matrix[3][0] + world_pos[1] * view_matrix[3][1] + world_pos[2] * view_matrix[3][2] + view_matrix[3][3]
    ])
    
    # Perspektif bölme (Clip space -> NDC)
    # w bileşeni sıfırdan büyük olmalı
    if vec4[3] < 0.001:
        return None  # Kamera arkasındaki nesneler
    
    # NDC koordinatları [-1, 1] aralığında
    ndc_x = vec4[0] / vec4[3]
    ndc_y = vec4[1] / vec4[3]
    
    # NDC -> Screen space
    # X: [-1,1] -> [0, width]
    # Y: [-1,1] -> [height, 0] (Y ekseni ters)
    screen_x = (screen_width / 2) * (ndc_x + 1)
    screen_y = (screen_height / 2) * (1 - ndc_y)
    
    # Ekran sınırları içinde mi kontrol et
    if screen_x < 0 or screen_x > screen_width or screen_y < 0 or screen_y > screen_height:
        return None
    
    return (screen_x, screen_y)

def world_to_screen_vectorized(world_positions: np.ndarray, view_matrix: np.ndarray,
                              screen_width: int = 1920, screen_height: int = 1080) -> np.ndarray:
    """
    Vektörize edilmiş World to Screen dönüşümü (çoklu pozisyonlar için)
    
    Args:
        world_positions: Nx3 boyutunda pozisyonlar
        view_matrix: 4x4 view matrisi
        screen_width: Ekran genişliği
        screen_height: Ekran yüksekliği
        
    Returns:
        np.ndarray: Nx2 boyutunda ekran koordinatları (görünmeyenler NaN)
    """
    if len(world_positions) == 0:
        return np.empty((0, 2))
    
    # Pozisyonları 4D vektörlere dönüştür (homojen koordinatlar)
    positions_4d = np.column_stack([world_positions, np.ones(len(world_positions))])
    
    # View matrix ile çarp (world -> clip)
    clip_positions = positions_4d @ view_matrix.T
    
    # Perspektif bölme (clip -> NDC)
    w = clip_positions[:, 3:4]
    valid = w > 0.001
    ndc = clip_positions / np.where(valid, w, 1)
    
    # NDC -> Screen
    screen = np.zeros((len(ndc), 2))
    screen[:, 0] = (screen_width / 2) * (ndc[:, 0] + 1)
    screen[:, 1] = (screen_height / 2) * (1 - ndc[:, 1])
    
    # Geçersiz noktaları NaN ile işaretle
    screen[~valid.flatten()] = np.nan
    
    return screen

def calculate_view_matrix(eye: np.ndarray, target: np.ndarray, up: np.ndarray = None) -> np.ndarray:
    """
    Göz, hedef ve up vektöründen view matrix hesaplar (eğitim amaçlı)
    
    Args:
        eye: Kamera pozisyonu
        target: Bakılan nokta
        up: Yukarı vektörü (varsayılan: [0, 1, 0])
        
    Returns:
        np.ndarray: 4x4 view matrix
    """
    if up is None:
        up = np.array([0, 1, 0])
    
    # Z ekseni (forward)
    z = (eye - target) / np.linalg.norm(eye - target)
    
    # X ekseni (right)
    x = np.cross(up, z)
    x = x / np.linalg.norm(x)
    
    # Y ekseni (up) - x ve z'ye dik
    y = np.cross(z, x)
    
    # View matrix
    view_matrix = np.zeros((4, 4))
    view_matrix[0, 0] = x[0]
    view_matrix[0, 1] = x[1]
    view_matrix[0, 2] = x[2]
    view_matrix[0, 3] = -np.dot(x, eye)
    
    view_matrix[1, 0] = y[0]
    view_matrix[1, 1] = y[1]
    view_matrix[1, 2] = y[2]
    view_matrix[1, 3] = -np.dot(y, eye)
    
    view_matrix[2, 0] = z[0]
    view_matrix[2, 1] = z[1]
    view_matrix[2, 2] = z[2]
    view_matrix[2, 3] = -np.dot(z, eye)
    
    view_matrix[3, 3] = 1.0
    
    return view_matrix

def get_bone_position_from_matrix(bone_matrix: np.ndarray, bone_index: int) -> np.ndarray:
    """
    Bone matrix'inden bone pozisyonunu çıkarır
    
    Args:
        bone_matrix: 4x4 bone matrix
        bone_index: Bone indeksi
        
    Returns:
        np.ndarray: (x, y, z) pozisyonu
    """
    if bone_matrix is None or len(bone_matrix) <= bone_index:
        return np.zeros(3)
    
    # Matrix'in son sütunun ilk 3 elemanı pozisyon
    bone_data = bone_matrix[bone_index]
    if isinstance(bone_data, np.ndarray):
        return bone_data[:3, 3]
    return np.zeros(3)
