import numpy as np

class RecoilControl:
    def __init__(self, intensity: float = 0.7):
        self.intensity = intensity
        self.last_punch = np.zeros(2)
    
    def update(self, current_punch):
        if current_punch is None:
            return np.zeros(2)
        punch = np.array(current_punch[:2], dtype=np.float32)
        compensation = -(punch - self.last_punch) * self.intensity
        self.last_punch = punch.copy()
        return compensation
    
    def reset(self):
        self.last_punch = np.zeros(2)
