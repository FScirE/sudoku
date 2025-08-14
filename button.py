import pygame

class Button:
    def __init__(self, pos, size, bg_color, fg_color, text, font, id, value = 0, hover_size_offset = 5):
        self.bounds = pygame.rect.Rect(pos[0], pos[1], size[0], size[1])

        self.color = [bg_color, fg_color] # options: "white, black, light, medium, dark"
        self.text = text
        self.font = font
        self.id = id
        self.value = value
        self.hover_size_offset = hover_size_offset

        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.bounds.collidepoint(mouse_pos)
        return self.is_hovered

    def draw(self, screen, color_table):
        bg_color = color_table[self.color[0]]
        fg_color = color_table[self.color[1]]
        text = self.font.render(self.text, True, fg_color)

        offset = self.hover_size_offset / 2
        if self.is_hovered:
            bounds = pygame.rect.Rect(
                self.bounds.left - offset,
                self.bounds.top - offset,
                self.bounds.width + offset * 2,
                self.bounds.height + offset * 2
            )
        else:
            bounds = self.bounds.copy()

        rectangle = text.get_rect(center = (
            self.bounds.x + self.bounds.width / 2,
            self.bounds.y + self.bounds.height / 2
        ))
        pygame.draw.rect(screen, bg_color, bounds)
        screen.blit(text, rectangle)
