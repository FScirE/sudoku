import pygame

class ProgressBar:
    def __init__(self, pos, size, bg_color, fg_color, progress = 0, max_progress = 100, border_radius = [-1, -1, -1, -1], shadow = None):
        self.progress = progress
        self.max_progress = max_progress

        self.bg_bounds = pygame.rect.Rect(pos[0], pos[1], size[0], size[1])
        self.set_fg_bounds()
        self.border_radius = border_radius

        self.color = [bg_color, fg_color] # options: "white, black, light, medium, dark"

        self.shadow = shadow

    def set_fg_bounds(self):
        self.fg_bounds = self.bg_bounds.copy()
        self.fg_bounds.width = self.bg_bounds.width * (self.progress / self.max_progress)

    def set_progress(self, progress):
        self.progress = progress
        self.set_fg_bounds()

    def draw(self, screen, color_table):
        if self.shadow is not None:
            self.shadow.draw(screen)

        bg_color = color_table[self.color[0]]
        fg_color = color_table[self.color[1]]
        pygame.draw.rect(
            screen,
            bg_color,
            self.bg_bounds,
            border_top_left_radius= self.border_radius[0],
            border_top_right_radius= self.border_radius[1],
            border_bottom_left_radius= self.border_radius[2],
            border_bottom_right_radius= self.border_radius[3]
        )
        pygame.draw.rect(
            screen,
            fg_color,
            self.fg_bounds,
            border_top_left_radius= self.border_radius[0],
            border_top_right_radius= self.border_radius[1],
            border_bottom_left_radius= self.border_radius[2],
            border_bottom_right_radius= self.border_radius[3]
        )
