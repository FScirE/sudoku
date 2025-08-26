import pygame
from PIL import Image, ImageFilter

class Shadow:
    def __init__(self, pos, size, strength, radius, border_radius = [-1, -1, -1, -1], offset = [0, 0], extra_size = 0):
        self.pos = [pos[0] + offset[0], pos[1] + offset[1]]
        self.size = [size[0] + extra_size, size[1] + extra_size]
        self.extra_size = extra_size
        self.strength = strength
        self.radius = radius
        self.border_radius = border_radius
        self.create_blur()

    def create_blur(self):
        rect = pygame.rect.Rect(self.radius * 2, self.radius * 2, self.size[0], self.size[1])
        surface = pygame.surface.Surface((self.size[0] + self.radius * 4, self.size[1] + self.radius * 4), pygame.SRCALPHA)
        pygame.draw.rect(surface, (0, 0, 0, self.strength), rect,
            border_top_left_radius= self.border_radius[0],
            border_top_right_radius= self.border_radius[1],
            border_bottom_left_radius= self.border_radius[2],
            border_bottom_right_radius= self.border_radius[3]
        )
        # blur using PIL
        pil_string = pygame.image.tostring(surface, "RGBA")
        pil_image = Image.frombuffer("RGBA", surface.get_size(), pil_string)
        pil_blur = pil_image.filter(ImageFilter.GaussianBlur(radius= self.radius))
        blurred = pygame.image.fromstring(pil_blur.tobytes(), pil_blur.size, pil_blur.mode)
        self.blurred = blurred.convert_alpha()

    def draw(self, screen):
        screen.blit(self.blurred, self.blurred.get_rect(center = 
            (self.pos[0] + (self.size[0] - self.extra_size) / 2,
            self.pos[1] + (self.size[1] - self.extra_size) / 2)
        ))
