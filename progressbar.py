import pygame

class ProgressBar:
    def __init__(self, pos, size, bg_color, fg_color, progress = 0, max_progress = 100):
        self.progress = progress
        self.max_progress = max_progress

        self.bg_bounds = pygame.rect.Rect(pos[0], pos[1], size[0], size[1])
        self.set_fg_bounds()

        self.color = [bg_color, fg_color] # options: "white, black, light, medium, dark"

    def set_fg_bounds(self):
        self.fg_bounds = self.bg_bounds.copy()
        self.fg_bounds.width = self.bg_bounds.width * (self.progress / self.max_progress)

    def set_progress(self, progress):
        self.progress = progress
        self.set_fg_bounds()

    def draw(self, screen, color_table):
        bg_color = color_table[self.color[0]]
        fg_color = color_table[self.color[1]]
        pygame.draw.rect(screen, bg_color, self.bg_bounds)
        pygame.draw.rect(screen, fg_color, self.fg_bounds)
