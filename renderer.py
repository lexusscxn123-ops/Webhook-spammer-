import pygame

class ESPRenderer:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def draw_box(self, screen, x, y, size, color, thickness=2):
        rect = pygame.Rect(int(x - size/2), int(y - size), int(size), int(size * 1.5))
        pygame.draw.rect(screen, color, rect, thickness)
