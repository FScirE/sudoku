import pygame
import threading
import copy
import sys
import pyperclip
from sudoku import Sudoku
from button import Button
from textbox import Textbox

# helper functions -------------------------

def tuple_sub(t1, t2):
    if len(t1) != len(t2):
        return t1
    return tuple([t1[i] - t2[i] for i in range(len(t1))])

def check_quit(events, threads = None, quit_signal = None):
    for event in events:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            if quit_signal is not None:
                quit_signal.set()
            if threads:
                screen.fill(white)
                text = font.render("Closing...", True, black)
                rectangle = text.get_rect(center = (width / 2, height / 2))
                screen.blit(text, rectangle)
                pygame.display.update()
                for t in threads:
                    t.join()
            pygame.quit()
            sys.exit()

def graphical_print(sudoku, notes, colors, current_light_color = None, selected = None):
    # draw cells
    for i in range(81):
        if colors[i] is not None:
            cell_color = color_table[colors[i]]
        else:
            cell_color = None
        cell_w = (width - padding["left"] - padding["right"]) / 9
        cell_h = (height - padding["top"] - padding["bottom"]) / 9
        # draw selected marking
        if selected is not None and i == selected and not sudoku.fixed[selected]:
            rect = pygame.rect.Rect(
                (i % 9) * cell_w + padding["left"],
                (i // 9) * cell_h + padding["top"],
                cell_w,
                cell_h
            )
            pygame.draw.rect(screen, current_light_color, rect)
        # draw notes
        cell_notes = notes[i]
        for note in cell_notes:
            note_col = (note - 1) % 3
            note_row = (note - 1) // 3
            text = small_font.render(f"{note}", True, cell_color[1])
            rectangle = text.get_rect(center = (
                (i % 9 + 0.5) * cell_w + padding["left"] + (note_col - 1) * (cell_w - note_padding * 2) // 3,
                (i // 9 + 0.5) * cell_h + padding["top"] + (1 - note_row) * (cell_h - note_padding * 2) // 3
            ))
            screen.blit(text, rectangle)
        # draw cell values
        value = sudoku.board[i]
        if value == 0:
            continue
        color = black if sudoku.fixed[i] else cell_color[2]
        text = font.render(f"{value}", True, color)
        rectangle = text.get_rect(center = (
            (i % 9 + 0.5) * cell_w + padding["left"],
            (i // 9 + 0.5) * cell_h + padding["top"]
        ))
        screen.blit(text, rectangle)
    # draw grid
    for i in range(10):
        if i % 3 == 0:
            line_width = 3
        else:
            line_width = 1
        pygame.draw.line(screen, black,
                        (i * (width - padding["left"] - padding["right"]) / 9 + padding["left"], padding["top"]),
                        (i * (width - padding["left"] - padding["right"]) / 9 + padding["left"], height - padding["bottom"]), line_width)
        pygame.draw.line(screen, black,
                        (padding["left"], i * (height - padding["top"] - padding["bottom"]) / 9 + padding["top"]),
                        (width - padding["right"], i * (height - padding["top"] - padding["bottom"]) / 9 + padding["top"]), line_width)
        
def draw_buttons(buttons):
    hovered = False
    for button in buttons:
        if not hovered and button.hovered(pygame.mouse.get_pos()):
            hovered = True
        button.draw(screen, current_color_table)
    if hovered:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
# game functions ---------------------------

def color_change(current_color, current_color_table):
    current_color = (current_color + 1) % len(color_table)
    current_color_table["light"] = color_table[current_color][0]
    current_color_table["medium"] = color_table[current_color][1]
    current_color_table["dark"] = color_table[current_color][2] 
    return current_color

def notes_toggle(note_mode, buttons):
    note_mode = not note_mode
    for button in buttons:
        if button.id.count("num_"):
            button.color[0] = "medium" if note_mode else "dark"
            button.color[1] = "black" if note_mode else "white"
        elif button.id == "notes":
            if note_mode:
                button.color[0] = "medium"
                button.color[1] = "black"
                button.text = "Notes: ON"
            else:
                button.color[0] = "dark"
                button.color[1] = "white"
                button.text = "Notes: OFF"
    return note_mode

def undo(history, sudoku, notes, colors):
    popped = history.pop()
    sudoku.board = popped[0]
    notes = popped[1]
    colors = popped[2]
    return notes, colors

def copy_board_info(sudoku, notes, colors):
    board_copy = sudoku.board[:]
    fixed_copy = sudoku.fixed[:]
    notes_copy = copy.deepcopy(notes)
    colors_copy = colors[:]
    return board_copy, fixed_copy, notes_copy, colors_copy

def add_to_history(history, sudoku, notes, colors, board_old, notes_old, colors_old):
    if sudoku.board == board_old and notes == notes_old and colors == colors_old:
        pass
    elif history and sudoku.board == history[-1][0] and notes == history[-1][1] and colors == history[-1][2]:
        history.pop()
    else:
        history.append((board_old, notes_old, colors_old))

def erase(sudoku, notes, colors, selected, history):
    board_old, _, notes_old, colors_old = copy_board_info(sudoku, notes, colors)

    sudoku.board[selected] = 0
    notes[selected] = []
    colors[selected] = None
   
    add_to_history(history, sudoku, notes, colors, board_old, notes_old, colors_old)  

def set_value(sudoku, notes, colors, selected, note_mode, number, history):
    board_old, _, notes_old, colors_old = copy_board_info(sudoku, notes, colors)

    if note_mode:
        if sudoku.board[selected]:
            return
        # add note
        if number not in notes[selected]:
            notes[selected].append(number)
            colors[selected] = current_color
        # remove note
        else:
            notes[selected].remove(number)
            if not notes[selected]:
                colors[selected] = None
    elif sudoku.board[selected] != number:
        sudoku.board[selected] = number
        notes[selected] = []
        colors[selected] = current_color

    add_to_history(history, sudoku, notes, colors, board_old, notes_old, colors_old)  

# setup ------------------------------------

# pygame setup
pygame.init()
pygame.display.set_caption("Sudoku")
width = 1000
height = 800
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

padding = {
    "top": 100, 
    "bottom": 100, 
    "left": 200, 
    "right": 200
}
note_padding = 4
font_size = 36
font = pygame.font.Font("arial/arial.ttf", font_size)
small_font = pygame.font.Font("arial/arial.ttf", font_size // 2)
narrow_font = pygame.font.Font("arial/arialn.ttf", font_size // 2)
large_font = pygame.font.Font("arial/arialbd.ttf", font_size * 2)

transparent_white = (255, 255, 255, 128)
white = (255, 255, 255)
black = (0, 0, 0)

# blue
blue_delta = (110, 70, 35)
light_blue = (225, 240, 255)
medium_blue = tuple_sub(light_blue, blue_delta)
dark_blue = tuple_sub(medium_blue, blue_delta)

# green
green_delta = (95, 50, 115)
light_green = (225, 255, 230)
medium_green = tuple_sub(light_green, green_delta)
dark_green = tuple_sub(medium_green, green_delta)

# red
red_delta = (35, 110, 75)
light_red = (250, 235, 235)
medium_red = tuple_sub(light_red, red_delta)
dark_red = tuple_sub(medium_red, red_delta)

color_table = {
    0: (light_blue, medium_blue, dark_blue),
    1: (light_green, medium_green, dark_green),
    2: (light_red, medium_red, dark_red)
}
color_names = {
    0: "Blue",
    1: "Green",
    2: "Red"
}

screen.fill(white)

# game -----------------------------------------

# program loop
sudoku = None
notes = None
colors = None
while True:

    # save current sudoku to be able to resume game
    try:
        saved_board, saved_fixed, saved_notes, saved_colors = copy_board_info(sudoku, notes, colors)
        saved_sudoku = Sudoku()
        saved_sudoku.board = saved_board
        saved_sudoku.fixed = saved_fixed
    except:
        saved_sudoku = saved_board = saved_fixed = saved_notes = saved_colors = None

    # sudoku setup
    sudoku = Sudoku()
    notes = [[] for _ in range(81)]
    colors = [None] * 81
    note_mode = False
    current_color = 0
    current_color_table = {
        "white": white,
        "black": black,
        "light": color_table[current_color][0],
        "medium": color_table[current_color][1],
        "dark": color_table[current_color][2]
    }
    selected = None
    difficulty = 0 # between 0-81 inclusive, higher -> easier
    code = ""

    # button and textbox setup for menu
    buttons = []
    # easy button
    button_width = 90
    button_height = 60
    buttons.append(
        Button(
            [width * 5 / 13 - button_width / 2, height * 19 / 40 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Easy",
            small_font,
            "generate",
            36
        )
    )
    # medium button
    button_width = 100
    button_height = 60
    buttons.append(
        Button(
            [width / 2 - button_width / 2, height * 19 / 40 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Medium",
            small_font,
            "generate",
            18
        )
    )
    # hard button
    button_width = 90
    button_height = 60
    buttons.append(
        Button(
            [width * 8 / 13 - button_width / 2, height * 19 / 40 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Hard",
            small_font,
            "generate",
            0
        )
    )
    # code input
    input_width = 680
    input_height = 50
    input = Textbox(
        [width / 2 - input_width / 2, height * 3 / 5 - input_height / 2],
        [input_width, input_height],
        "medium",
        "black",
        narrow_font,
        "code_input"
    )
    # from code button
    button_width = 160
    button_height = 60
    buttons.append(
        Button(
            [width / 2 - button_width / 2, height * 7 / 10 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Import Sudoku",
            small_font,
            "code_finished"
        )
    )
    # resume button
    if saved_sudoku is not None and not saved_sudoku.full():
        button_width = 100
        button_height = 50
        buttons.append(
            Button(
                [0, 0],
                [button_width, button_height],
                "medium",
                "white",
                "Resume",
                small_font,
                "resume"
            )
        )

    # menu screen
    generate = False
    resume_game = False
    pre_game_loop = True
    while pre_game_loop:
        screen.fill(white)

        text = large_font.render("SUDOKU", True, black)
        text_u = font.render("Generate Sudoku", True, black)
        rectangle = text.get_rect(center = (width / 2, height / 4))
        rectangle_u = text_u.get_rect(center = (width / 2, height * 2 / 5))
        screen.blit(text, rectangle)
        screen.blit(text_u, rectangle_u)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if saved_sudoku is not None and not saved_sudoku.full():
                    pre_game_loop = False
                    resume_game = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                for button in buttons:
                    if button.hovered(event.pos):
                        if button.id == "generate":
                            pre_game_loop = False
                            generate = True
                            difficulty = button.value
                        elif button.id == "code_finished":
                            pre_game_loop = False
                        elif button.id == "resume":
                            pre_game_loop = False
                            resume_game = True
                if input.hovered(event.pos):
                    input.active = True
                else:
                    input.active = False

        if input.handle_input(events):
            pre_game_loop = False

        # check if code gave a valid sudoku
        if not pre_game_loop and not generate and not resume_game:
            if not sudoku.from_string(input.content):
                pre_game_loop = True
                input.content = ""

        draw_buttons(buttons)

        if pygame.mouse.get_cursor().data[0] == pygame.SYSTEM_CURSOR_ARROW and input.hovered(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
        input.draw(screen, current_color_table)

        check_quit(events)

        pygame.display.update()
        clock.tick(30)

    if generate:
        # generate random sudoku
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_WAIT)

        print("Generating completed board...")
        sudoku.generate_completed_board()

        print("Removing numbers...")
        quit_signal = threading.Event()
        thread = threading.Thread(target=sudoku.remove_board_numbers, args=(difficulty,), kwargs={"quit_signal": quit_signal,})
        thread.start()
        while thread.is_alive():
            screen.fill(white)

            text_g = font.render("Solved sudoku generated", True, black)
            text_r = font.render("Removing numbers...", True, black)
            sudoku.atomic_lock.acquire()
            print(f"Remaining: {sudoku.atomic_counter} ", end="\r")
            text_p = font.render(f"Remaining: {sudoku.atomic_counter}", True, black)
            sudoku.atomic_lock.release()
            rectangle_g = text_g.get_rect(center = (width / 2, height / 2 - (font_size + 8)))
            rectangle_r = text_r.get_rect(center = (width / 2, height / 2))
            rectangle_p = text_p.get_rect(center = (width / 2, height / 2 + (font_size + 8)))
            screen.blit(text_g, rectangle_g)
            screen.blit(text_r, rectangle_r)
            screen.blit(text_p, rectangle_p)

            events = pygame.event.get()
            check_quit(events, [thread], quit_signal)

            pygame.display.update()
            clock.tick(30)
        print("\r             ")

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    elif resume_game:
        print(f"Resume game")
        sudoku = saved_sudoku
        notes = saved_notes
        colors = saved_colors
    else:
        print(f"Generated from code: {input.content}\n")

    code = sudoku.to_string()
    sudoku.print()
    print(f"Code: {code}")
    history = []   

    # button setup for game
    buttons = []
    # number buttons
    button_spacing = 12
    button_width = (width - padding["left"] - padding["right"]) / 9
    button_height = button_width 
    for n in range(1, 10):
        pos_x = padding["left"] - button_spacing * 4 + (n - 1) * (button_width + button_spacing)
        pos_y = padding["top"] / 2 - button_height / 2
        buttons.append(
            Button(
                [pos_x, pos_y], 
                [button_width, button_height],
                "dark",
                "white",
                f"{n}",
                small_font,
                f"num_{n}",
                n
            )
        )
    # color button
    button_width = 140
    button_height = 50
    buttons.append(
        Button(
            [width * 5 / 14 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Change Color",
            small_font,
            "color",
        )
    )
    # note mode button
    button_width = 115
    button_height = 50
    buttons.append(
        Button(
            [width / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Notes: OFF",
            small_font,
            "notes",
        )
    )
    # undo button
    button_width = 70
    button_height = 50
    buttons.append(
        Button(
            [width * 5 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Undo",
            small_font,
            "undo",
        )
    )
    # erase button
    button_width = 75
    button_height = 50
    buttons.append(
        Button(
            [width * 6 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Erase",
            small_font,
            "erase",
        )
    )
    # copy button
    button_width = 70
    button_height = 50
    buttons.append(
        Button(
            [width * 11 / 20 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Copy",
            small_font,
            "copy",
        )
    )
    # back button
    button_width = 70
    button_height = 50
    buttons.append(
        Button(
            [0, 0],
            [button_width, button_height],
            "medium",
            "white",
            "Back",
            small_font,
            "back",
        )
    )

    # game loop
    return_menu = False
    while True:
        screen.fill(white)

        if sudoku.full():
            if sudoku.valid():
                break
            else:
                pass

        events = pygame.event.get()
        for event in events:
            # keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    current_color = color_change(current_color, current_color_table)
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    note_mode = notes_toggle(note_mode, buttons)
                elif event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
                    if history:
                        notes, colors = undo(history, sudoku, notes, colors)
                elif event.key == pygame.K_c and event.mod & pygame.KMOD_CTRL:
                    pyperclip.copy(code)
                elif event.key == pygame.K_ESCAPE:
                    # go back to menu (override quit)
                    return_menu = True
                    break
                elif selected is not None and not sudoku.fixed[selected]:
                    # erasing
                    if event.key in [pygame.K_BACKSPACE, pygame.K_SPACE, pygame.K_0, pygame.K_KP0]:
                        erase(sudoku, notes, colors, selected, history)
                    # setting number
                    elif pygame.K_1 <= event.key <= pygame.K_9 or pygame.K_KP0 <= event.key <= pygame.K_KP9:
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            number = event.key - pygame.K_0
                        else:
                            number = event.key - pygame.K_KP0
                        set_value(sudoku, notes, colors, selected, note_mode, number, history)
            # mouse events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # left click
                    board_bounds = pygame.rect.Rect(
                        padding["left"], 
                        padding["top"], 
                        width - padding["left"] - padding["right"], 
                        height - padding["top"] - padding["bottom"]
                    )
                    # check buttons
                    button_pressed = False
                    for button in buttons:
                        if button.hovered(event.pos):
                            if button.id == "color":
                                current_color = color_change(current_color, current_color_table)
                                button_pressed = True
                            elif button.id == "notes":
                                note_mode = notes_toggle(note_mode, buttons)
                                button_pressed = True
                            elif button.id == "undo":
                                if history:
                                    notes, colors = undo(history, sudoku, notes, colors)
                                button_pressed = True
                            elif button.id == "erase":
                                if selected:
                                    erase(sudoku, notes, colors, selected, history)
                                button_pressed = True
                            elif button.id == "copy":
                                pyperclip.copy(code)
                            elif button.id == "back":
                                return_menu = True
                                break
                            elif button.id.count("num_"):
                                if selected:
                                    number = button.value
                                    set_value(sudoku, notes, colors, selected, note_mode, number, history)
                                button_pressed = True
                    # check board
                    if not button_pressed:
                        selected = None
                    if board_bounds.collidepoint(event.pos):
                        row = ((event.pos[1] - padding["top"]) * 9) // (height - padding["top"] - padding["bottom"])
                        col = ((event.pos[0] - padding["left"]) * 9) // (width - padding["left"] - padding["right"])
                        selected = row * 9 + col                       
                elif event.button == 3:
                    selected = None
        
        if return_menu:
            break

        graphical_print(sudoku, notes, colors, current_color_table["light"], selected)

        draw_buttons(buttons)

        check_quit(events)

        pygame.display.update()
        clock.tick(60)

    # skip win screen
    if return_menu:
        continue

    # button setup post game
    current_color_table = {
        "white": white,
        "black": black,
        "light": light_blue,
        "medium": medium_blue,
        "dark": dark_blue
    }
    buttons = []
    # return button
    button_width = 155
    button_height = 50
    buttons.append(
        Button(
            [width * 3 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Return To Menu",
            small_font,
            "menu"
        )
    )
    # copy button
    button_width = 70
    button_height = 50
    buttons.append(
        Button(
            [width * 4 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2],
            [button_width, button_height],
            "dark",
            "white",
            "Copy",
            small_font,
            "copy",
        )
    )

    # win screen
    win_screen_loop = True
    while win_screen_loop:
        screen.fill(white)

        graphical_print(sudoku, notes, colors)

        layer = pygame.surface.Surface((width, height), pygame.SRCALPHA)
        layer.fill(transparent_white)
        screen.blit(layer, (0, 0))

        text = font.render("Congratulations!", True, black)
        rectangle = text.get_rect(center = (width / 2, padding["top"] / 2))
        screen.blit(text, rectangle)

        events = pygame.event.get()
        for event in events:
            # new game
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    win_screen_loop = False
                elif event.key == pygame.K_c and event.mod & pygame.KMOD_CTRL:
                    pyperclip.copy(code)
            elif event.type == pygame.MOUSEBUTTONDOWN: 
                if event.button == 1:
                    for button in buttons:
                        if button.hovered(event.pos):
                            if button.id == "menu":
                                win_screen_loop = False
                                break
                            elif button.id == "copy":
                                pyperclip.copy(code)

        draw_buttons(buttons)

        check_quit(events)

        pygame.display.update()
        clock.tick(30)
