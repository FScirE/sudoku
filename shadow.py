import pygame
import math

class Shadow:
    def __init__(self, pos, size, strength, radius, border_radius = [-1, -1, -1, -1], offset = [0, 0], extra_size = 0, resolution = 20):
        self.pos = [pos[0] + offset[0] - extra_size / 2, pos[1] + offset[1] - extra_size / 2]
        self.size = [size[0] + extra_size, size[1] + extra_size]
        self.strength = strength
        self.radius = radius
        self.border_radius = border_radius
        self.resolution = resolution
        self.create_layers()

    def create_layers(self):
        self.layers = []
        max_opacity = self.strength
        min_opacity = 4
        # set border radius relative to width
        if self.border_radius == [-1, -1, -1, -1]:
            border_radius_fractions = self.border_radius
        else:
            border_radius_fractions = [
                self.border_radius[0] / self.size[0],
                self.border_radius[1] / self.size[0],
                self.border_radius[2] / self.size[0],
                self.border_radius[3] / self.size[0]
            ]
        # math for shadow opacity curve (opacity = ax^2 + bx + c)
        a = (min_opacity - max_opacity) / ((self.resolution - 1) ** 2)
        b = -2 * a * (self.resolution - 1)
        c = min_opacity
        f = lambda x: a * (x ** 2) + b * x + c
        # create layers
        for i in range(self.resolution):
            opacity = f(i)
            pos = [x + i * ((self.radius / 2) / (self.resolution - 1)) for x in self.pos]
            size = [x - i * (self.radius / (self.resolution - 1)) for x in self.size]
            self.layers.append((
                pygame.rect.Rect(pos[0], pos[1], size[0], size[1]),
                (255 - opacity, 255 - opacity, 255 - opacity),
                [round(x * size[0]) for x in border_radius_fractions]
            ))

    def draw(self, screen):
        for l in self.layers:
            rectangle = l[0]
            color = l[1]
            border_radius = l[2]
            pygame.draw.rect(
                screen,
                color,
                rectangle,
                border_top_left_radius= border_radius[0],
                border_top_right_radius= border_radius[1],
                border_bottom_left_radius= border_radius[2],
                border_bottom_right_radius= border_radius[3]
            )
