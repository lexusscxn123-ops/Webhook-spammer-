import numpy as np
import math

def calc_angle(local_pos: np.ndarray, target_pos: np.ndarray):
    delta = target_pos - local_pos
    yaw = math.atan2(delta[1], delta[0]) * 180 / math.pi
    pitch = -math.atan2(delta[2], np.sqrt(delta[0]**2 + delta[1]**2)) * 180 / math.pi
    return (yaw, pitch)

def smooth_angle(current: np.ndarray, target: np.ndarray, smoothness: float):
    factor = 1.0 / smoothness if smoothness > 0 else 1.0
    return current + (target - current) * min(factor, 1.0)

def get_fov(current_angles: np.ndarray, target_angles: np.ndarray):
    delta = target_angles - current_angles
    return math.sqrt(delta[0]**2 + delta[1]**2)
