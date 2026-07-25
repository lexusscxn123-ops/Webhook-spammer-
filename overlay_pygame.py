import pygame
import logging

logger = logging.getLogger(__name__)

class PygameESPOverlay:
    def __init__(self, entity_manager, view_matrix_getter, screen_width=1920, screen_height=1080):
        self.entity_manager = entity_manager
        self.view_matrix_getter = view_matrix_getter
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.running = False
        
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME | pygame.SRCALPHA)
        pygame.display.set_caption("ESP Overlay")
    
    def run(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
            
            self.screen.fill((0, 0, 0, 0))
            pygame.display.flip()
        
        pygame.quit()
    
    def close(self):
        self.running = False
        pygame.quit()
