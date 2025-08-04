import pyperclip
import pygame

class Textbox:
    def __init__(self, pos, size, bg_color, fg_color, font, id):
        self.bounds = pygame.rect.Rect(pos[0], pos[1], size[0], size[1])

        self.color = [bg_color, fg_color] # options: "white, black, light, medium, dark"
        self.content = ""
        self.font = font
        self.id = id
        self.active = False

    def handle_input(self, events):
        if not self.active:
            return False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL: 
                    content = pyperclip.paste()
                    content = content.replace("\r", "")
                    content = content.replace("\n", "")
                    content = content.replace(" ", "")
                    self.content += content
                    if len(self.content) > 82:
                        self.content = self.content[:82]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    if event.mod & pygame.KMOD_CTRL:
                        self.content = ""
                    else:
                        self.content = self.content[:-1]
                else:
                    self.content += event.unicode
                    self.content = self.content.replace("\x1a", "")
                    if len(self.content) > 82:
                        self.content = self.content[:82]
        return False

    def hovered(self, mouse_pos):
        return self.bounds.collidepoint(mouse_pos)
    
    def draw(self, screen, color_table):
        bg_color = color_table[self.color[0]]
        fg_color = color_table[self.color[1]]
        text = self.font.render(self.content, True, fg_color)
        rectangle: pygame.rect.Rect = text.get_rect(center = (
            self.bounds.x + self.bounds.width / 2,
            self.bounds.y + self.bounds.height / 2
        ))
        pygame.draw.rect(screen, bg_color, self.bounds)
        if self.active:
            pygame.draw.line(screen, fg_color, rectangle.topright, rectangle.bottomright, 2)
        screen.blit(text, rectangle)
