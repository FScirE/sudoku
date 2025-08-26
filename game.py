import pygame
import threading
import copy
import sys
import pyperclip
import os
import json
from sudoku import Sudoku, conflicts
from button import Button
from textbox import Textbox
from progressbar import ProgressBar
from shadow import Shadow

# helper functions -------------------------

def tuple_sub(t1, t2):
    if len(t1) != len(t2):
        return t1
    return tuple([t1[i] - t2[i] for i in range(len(t1))])

def check_quit(events, threads = None, quit_signal = None, sudoku = None, notes = None, colors = None, history = None, ignore_esc = False):
    for event in events:
        if event.type == pygame.QUIT or (not ignore_esc and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
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
            if None not in [sudoku, notes, colors, history]:
                write_savegame(sudoku.board, sudoku.fixed, notes, colors, history)
            pygame.quit()
            sys.exit()

def draw_stripes(color, factor, thickness, left, top, width, height, flipped = False):
    for n in range(1, factor):
        pygame.draw.line(
            screen, 
            color,
            (left, top + (factor - n if flipped else n) * (height / factor)),
            (left + n * (width / factor), top + (height if flipped else 0)),
            thickness
        )  
    for n in range(factor):
        pygame.draw.line(
            screen,
            color,
            (left + n * (width / factor), top + (0 if flipped else height)),
            (left + width, top + (factor - n if flipped else n) * (height / factor)),
            thickness
        )

def graphical_print(sudoku, notes, colors, current_light_color = None, selected = None, shadow = None):
    # draw shadow
    if shadow is not None:
        shadow.draw(screen)
    # draw cells
    for i in range(81):
        value = sudoku.board[i]
        if colors[i] is not None:
            cell_color = color_table[colors[i]]
        else:
            cell_color = None
        cell_w = (width - padding["left"] - padding["right"]) / 9
        cell_h = (height - padding["top"] - padding["bottom"]) / 9
        cell_left = (i % 9) * cell_w + padding["left"]
        cell_top = (i // 9) * cell_h + padding["top"]
        # draw selected marking
        cell_bg = white
        if selected is not None and i == selected:
            cell_bg = current_light_color     
        rect = pygame.rect.Rect(cell_left, cell_top, cell_w, cell_h)
        pygame.draw.rect(screen, cell_bg, rect)
        # conflicting cells marked
        if value != 0 and conflicts(sudoku.board, i, value):      
            draw_stripes(gray, 6, 3, cell_left, cell_top, cell_w, cell_h, True)  
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
        if value == 0:
            continue
        color = black if sudoku.fixed[i] else cell_color[2]
        cell_font = bold_font if sudoku.fixed[i] else font
        text = cell_font.render(f"{value}", True, color)
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
            (i * (width - padding["left"] - padding["right"]) / 9 + padding["left"], height - padding["bottom"]), 
            line_width
        )
        pygame.draw.line(screen, black,
            (padding["left"], i * (height - padding["top"] - padding["bottom"]) / 9 + padding["top"]),
            (width - padding["right"], i * (height - padding["top"] - padding["bottom"]) / 9 + padding["top"]), 
            line_width
        )

def update_buttons(buttons):
    # update the hovered state of all buttons and return hovered button
    hovered = None
    for button in buttons:
        if button.update():
            hovered = button
    if hovered is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    return hovered

def draw_buttons(buttons, surface):
    for button in buttons:
        button.draw(surface, current_color_table) 

def create_default_shadow(pos, size, border_radius = [-1, -1, -1, -1], extra_offset = [0, 0], extra_extra_size = 0, extra_radius = 0):
    strength = 80
    radius = 3 + extra_radius
    offset = [2 + extra_offset[0], 2 + extra_offset[1]]
    extra_size = extra_extra_size
    return Shadow(pos, size, strength, radius, border_radius, offset, extra_size)

def write_savegame(board, fixed, notes, colors, history):
    try:
        file = open("./savegame.json", "w")
        data = {
            "board": board,
            "fixed": fixed,
            "notes": notes,
            "colors": colors,
            "history": history
        }
        json.dump(data, file, indent= 4)
    except:
        return False
    return True

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
    index = popped[0]
    sudoku.board[index] = popped[1]
    notes[index] = popped[2]
    colors[index] = popped[3]
    return notes, colors

def copy_board_info(sudoku, notes, colors):
    board_copy = sudoku.board[:]
    fixed_copy = sudoku.fixed[:]
    notes_copy = copy.deepcopy(notes)
    colors_copy = colors[:]
    return board_copy, fixed_copy, notes_copy, colors_copy

def add_to_history(history, new_board_info, old_board_info):
    if new_board_info == old_board_info:
        return
    else:
        # get index of changed cell
        board_diff_index = -1
        for i in range(len(new_board_info[0])):
            if new_board_info[0][i] != old_board_info[0][i]:
                board_diff_index = i
                break
        notes_diff_index = -1
        for i in range(len(new_board_info[1])):
            if new_board_info[1][i] != old_board_info[1][i]:
                notes_diff_index = i
                break
        diff_index = board_diff_index if board_diff_index != -1 else notes_diff_index
        # store old board information
        old_value = old_board_info[0][diff_index]
        old_notes = old_board_info[1][diff_index]
        old_color = old_board_info[2][diff_index]
        # add to history
        history.append((diff_index, old_value, old_notes, old_color))

def erase(sudoku, notes, colors, selected, history):
    board_old, _, notes_old, colors_old = copy_board_info(sudoku, notes, colors)

    sudoku.board[selected] = 0
    notes[selected] = []
    colors[selected] = None

    add_to_history(history, (sudoku.board, notes, colors), (board_old, notes_old, colors_old))

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

    add_to_history(history, (sudoku.board, notes, colors), (board_old, notes_old, colors_old))

# transitions ------------------------------

def fade(is_out, time, sudoku = None, notes = None, colors = None, grid_shadow = None, buttons = None, current_color_table = None, text_rects = None, sudoku_overlay = None, extra_surface = None):
    # time is amount of frames to finish fading
    time_start = time
    while time > 0:
        screen.fill(white)

        if None not in [sudoku, notes, colors]:
            graphical_print(sudoku, notes, colors, shadow= grid_shadow)
        if sudoku_overlay is not None:
            screen.blit(sudoku_overlay, (0, 0))
        if None not in [buttons, current_color_table]:
            for b in buttons:
                b.draw(screen, current_color_table)
        if text_rects is not None:
            for t in text_rects:
                screen.blit(t[0], t[1])
        if extra_surface is not None:
            screen.blit(extra_surface, (0, 0))

        alpha = (1 - (time / time_start)) * 255 if is_out else (time / time_start) * 255
        overlay_color = (255, 255, 255, alpha)
        layer = pygame.surface.Surface((width, height), pygame.SRCALPHA)
        layer.fill(overlay_color)
        screen.blit(layer, (0, 0))


        # disabled because of saving game not working properly with this
        # events = pygame.event.get()
        # check_quit(events) 
        _ = pygame.event.get() # keep this for window not to freeze

        time -= 1
        pygame.display.update()
        clock.tick(60)

# setup ------------------------------------

# pygame setup
pygame.init()
pygame.display.set_caption("Sudoku")
icon = pygame.image.load("resources/icon.ico")
pygame.display.set_icon(icon)
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
font = pygame.font.Font("resources/arial.ttf", font_size)
bold_font = pygame.font.Font("resources/arialbd.ttf", font_size)
small_font = pygame.font.Font("resources/arial.ttf", font_size // 2)
narrow_font = pygame.font.Font("resources/arialn.ttf", font_size // 2)
large_font = pygame.font.Font("resources/arialbd.ttf", font_size * 2)

border_radius = [8, 8, 8, 8]
corner_border_radius = [0, 0, 0, 8]

transparent_white = (255, 255, 255, 128)
white = (255, 255, 255)
gray = (200, 200, 200)
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

sudoku = None
notes = None
colors = None
history = None

# load stored game if exists
if os.path.exists("./savegame.json"):
    file = open("./savegame.json", "r")
    data = json.load(file)
    sudoku = Sudoku()
    sudoku.board = data["board"]
    sudoku.fixed = data["fixed"]
    notes = data["notes"]
    colors = data["colors"]
    history = data["history"]
    print("Loaded game from file")

# program loop
while True:

    # save current sudoku to be able to resume game
    try:
        saved_board, saved_fixed, saved_notes, saved_colors = copy_board_info(sudoku, notes, colors)
        saved_sudoku = Sudoku()
        saved_sudoku.board = saved_board
        saved_sudoku.fixed = saved_fixed
        saved_history = copy.deepcopy(history)
    except:
        saved_sudoku = saved_board = saved_fixed = saved_notes = saved_colors = saved_history = None

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
    history = []

    # button and textbox setup for menu
    buttons = []
    # select difficulty button
    button_width = 160
    button_height = 60
    pos = [width / 2 - button_width / 2, height * 19 / 40 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Select Difficulty",
            small_font,
            "select",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # code input
    input_width = 680
    input_height = 50
    pos = [width / 2 - input_width / 2, height * 3 / 5 - input_height / 2]
    size = [input_width, input_height]
    input = Textbox(
        pos,
        size,
        "medium",
        "black",
        narrow_font,
        "code_input",
        border_radius= border_radius,
        shadow= create_default_shadow(pos, size, border_radius)
    )
    # from code button
    button_width = 160
    button_height = 60
    pos = [width / 2 - button_width / 2, height * 7 / 10 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Import Sudoku",
            small_font,
            "code_finished",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # resume button
    if saved_sudoku is not None and not saved_sudoku.full():
        button_width = 100
        button_height = 50
        pos = [0, 0]
        size = [button_width, button_height]
        buttons.append(
            Button(
                pos,
                size,
                "medium",
                "white",
                "Resume",
                small_font,
                "resume",
                border_radius= corner_border_radius,
                shadow= create_default_shadow(pos, size, corner_border_radius, [-4, -4], 4)
            )
        )

    # difficulty selection setup
    selection_buttons = []
    selection_menu = False
    selection_width = 460
    selection_height = 300
    text_s = font.render("Select Difficulty", True, black)
    rectangle_s = text_s.get_rect(center = (width / 2, height * 2 / 5))
    # easy button
    button_width = 90
    button_height = 60
    pos = [width * 5 / 13 - button_width / 2, height / 2 - button_height / 2]
    size = [button_width, button_height]
    selection_buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Easy",
            small_font,
            "generate",
            36,
            border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # medium button
    button_width = 100
    button_height = 60
    pos = [width / 2 - button_width / 2, height / 2 - button_height / 2]
    size = [button_width, button_height]
    selection_buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Medium",
            small_font,
            "generate",
            18,
            border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # hard button
    button_width = 90
    button_height = 60
    pos = [width * 8 / 13 - button_width / 2, height / 2 - button_height / 2]
    size = [button_width, button_height]
    selection_buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Hard",
            small_font,
            "generate",
            0,
            border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # close button
    button_width = 105
    button_height = 60
    pos = [width / 2 - button_width / 2, height * 3 / 5 - button_height / 2]
    size = [button_width, button_height]
    selection_buttons.append(
        Button(
            pos,
            size,
            "medium",
            "white",
            "Close",
            small_font,
            "close",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # selection menu shadow
    selection_shadow = create_default_shadow(
        ((width - selection_width) / 2, (height - selection_height) / 2),
        (selection_width, selection_height),
        border_radius,
        extra_extra_size= 4,
        extra_radius= 1
    )

    # menu screen text
    text = large_font.render("SUDOKU", True, black)
    text_u = font.render("Generate Sudoku", True, black)
    rectangle = text.get_rect(center = (width / 2, height / 4))
    rectangle_u = text_u.get_rect(center = (width / 2, height * 2 / 5))

    # fade in before menu
    fade(False, 10, buttons= buttons + [input], current_color_table= current_color_table, text_rects= [(text, rectangle), (text_u, rectangle_u)])

    # menu screen
    generate = False
    resume_game = False
    pre_game_loop = True
    while pre_game_loop:
        screen.fill(white)

        screen.blit(text, rectangle)
        screen.blit(text_u, rectangle_u)

        button = update_buttons(selection_buttons if selection_menu else buttons)

        selection_menu_closed = False

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:            
                if event.key == pygame.K_r:
                    if saved_sudoku is not None and not saved_sudoku.full():
                        pre_game_loop = False
                        resume_game = True
                elif selection_menu and event.key == pygame.K_ESCAPE:
                    selection_menu = False
                    selection_menu_closed = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button is not None:
                    if button.id == "generate":
                        pre_game_loop = False
                        generate = True
                        difficulty = button.value
                    elif button.id == "code_finished":
                        pre_game_loop = False
                    elif button.id == "resume":
                        pre_game_loop = False
                        resume_game = True
                    elif button.id == "select":
                        selection_menu = True
                    elif button.id == "close":
                        selection_menu = False
                else:
                    if input.hovered(event.pos):
                        input.active = True
                    else:
                        input.active = False

        if not selection_menu and input.handle_input(events):
            pre_game_loop = False

        # check if code gave a valid sudoku
        if not pre_game_loop and not generate and not resume_game:
            if not sudoku.from_string(input.content):
                pre_game_loop = True
                input.content = ""

        draw_buttons(buttons, screen)

        if pygame.mouse.get_cursor().data[0] == pygame.SYSTEM_CURSOR_ARROW and input.hovered(pygame.mouse.get_pos()) and not selection_menu:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
        input.draw(screen, current_color_table)

        # draw selection menu overlay
        if selection_menu:
            layer = pygame.surface.Surface((width, height), pygame.SRCALPHA)
            layer.fill(transparent_white)
            selection_shadow.draw(layer)
            menu_rect = pygame.rect.Rect(
                (width - selection_width) / 2,
                (height - selection_height) / 2,
                selection_width,
                selection_height
            )
            pygame.draw.rect(layer, white, menu_rect, 
                border_top_left_radius= border_radius[0],
                border_top_right_radius= border_radius[1],
                border_bottom_left_radius= border_radius[2],
                border_bottom_right_radius= border_radius[3]
            )
            layer.blit(text_s, rectangle_s)         
            draw_buttons(selection_buttons, layer)
            screen.blit(layer, (0, 0))

        check_quit(events, sudoku= saved_sudoku, notes= saved_notes, colors= saved_colors, history= saved_history, ignore_esc= selection_menu_closed)

        pygame.display.update()
        clock.tick(30)

    # fade out before generation / sudoku start
    fade(True, 10, buttons= buttons + [input], current_color_table= current_color_table, text_rects= [(text, rectangle), (text_u, rectangle_u)], extra_surface= (layer if generate else None))

    if generate:
        # generate random sudoku
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_WAIT)

        print("Generating completed board...")
        sudoku.generate_completed_board()
        text = font.render("Generating solved sudoku", True, black)
        rectangle = text.get_rect(center = (width / 2, height / 2 - (font_size + 8)))
        # fade in for generation
        fade(False, 10, text_rects= [(text, rectangle)])

        # create progress bar
        bar_width = 680
        bar_height = 20
        pos = [width / 2 - bar_width / 2, height * 2 / 3 - bar_height / 2]
        size = [bar_width, bar_height]
        progress_bar = ProgressBar(
            pos,
            size,
            "medium",
            "dark",
            difficulty,
            81,
            border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )

        print("Removing numbers...")
        quit_signal = threading.Event()
        thread = threading.Thread(target=sudoku.remove_board_numbers, args=(difficulty, True), kwargs={"quit_signal": quit_signal,})
        thread.start()
        while thread.is_alive():
            screen.fill(white)

            text_g = font.render("Solved sudoku generated", True, black)
            text_r = font.render("Removing numbers...", True, black)
            sudoku.atomic_lock.acquire()
            counter = sudoku.atomic_counter
            sudoku.atomic_lock.release()
            print(f"Remaining: {counter} ", end="\r")
            text_p = font.render(f"Remaining: {counter}", True, black)

            rectangle_g = text_g.get_rect(center = (width / 2, height / 2 - (font_size + 8)))
            rectangle_r = text_r.get_rect(center = (width / 2, height / 2))
            rectangle_p = text_p.get_rect(center = (width / 2, height / 2 + (font_size + 8)))

            screen.blit(text_g, rectangle_g)
            screen.blit(text_r, rectangle_r)
            screen.blit(text_p, rectangle_p)

            progress_bar.set_progress(81 - counter)
            progress_bar.draw(screen, current_color_table)

            events = pygame.event.get()
            check_quit(events, [thread], quit_signal, saved_sudoku, saved_notes, saved_colors, saved_history)

            pygame.display.update()
            clock.tick(60)
        print("\r             ")

        # finished generating text (only shows during transition)
        screen.fill(white)
        text_g = font.render("Solved sudoku generated", True, black)
        text_r = font.render("Finished Removing Numbers", True, black)
        text_p = font.render(f"Remaining: 0", True, black)
        rectangle_g = text_g.get_rect(center = (width / 2, height / 2 - (font_size + 8)))
        rectangle_r = text_r.get_rect(center = (width / 2, height / 2))
        rectangle_p = text_p.get_rect(center = (width / 2, height / 2 + (font_size + 8)))
        screen.blit(text_g, rectangle_g)
        screen.blit(text_r, rectangle_r)
        screen.blit(text_p, rectangle_p)
        progress_bar.set_progress(81)
        progress_bar.draw(screen, current_color_table)
        pygame.display.update()

        # fade out after generation
        fade(True, 10, buttons= [progress_bar], current_color_table= current_color_table, text_rects= [(text_g, rectangle_g), (text_r, rectangle_r), (text_p, rectangle_p)])

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    elif resume_game:
        print(f"Resume game")
        sudoku = saved_sudoku
        notes = saved_notes
        colors = saved_colors
        history = saved_history
    else:
        print(f"Generated from code: {input.content}\n")

    code = sudoku.to_string()
    sudoku.print()
    print(f"Code: {code}")

    # button setup for game
    buttons = []
    # number buttons
    button_spacing = 12
    button_width = (width - padding["left"] - padding["right"]) / 9
    button_height = button_width
    for n in range(1, 10):
        pos_x = padding["left"] - button_spacing * 4 + (n - 1) * (button_width + button_spacing)
        pos_y = padding["top"] / 2 - button_height / 2
        pos = [pos_x, pos_y]
        size = [button_width, button_height]
        # create button for number
        buttons.append(
            Button(
                pos,
                size,
                "dark",
                "white",
                f"{n}",
                small_font,
                f"num_{n}",
                n,
                border_radius,
                shadow= create_default_shadow(pos, size, border_radius)
            )
        )
    # color button
    button_width = 140
    button_height = 50
    pos = [width * 5 / 14 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Change Color",
            small_font,
            "color",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # note mode button
    button_width = 115
    button_height = 50
    pos = [width / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Notes: OFF",
            small_font,
            "notes",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # undo button
    button_width = 70
    button_height = 50
    pos = [width * 5 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Undo",
            small_font,
            "undo",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # erase button
    button_width = 75
    button_height = 50
    pos = [width * 6 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Erase",
            small_font,
            "erase",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # copy button
    button_width = 70
    button_height = 50
    pos = [width * 11 / 20 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Copy",
            small_font,
            "copy",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # back button
    button_width = 70
    button_height = 50
    pos = [0, 0]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "medium",
            "white",
            "Back",
            small_font,
            "back",
            border_radius= corner_border_radius,
            shadow= create_default_shadow(pos, size, corner_border_radius, [-4, -4], 4)
        )
    )

    # shadow for sudoku grid
    grid_shadow = create_default_shadow(
        [padding["left"], padding["top"]],
        [width - padding["left"] - padding["right"], height - padding["top"] - padding["bottom"]],
        extra_offset= [2, 2],
        extra_extra_size= 2
    )

    # fade in for game
    fade(False, 10, sudoku, notes, colors, grid_shadow, buttons, current_color_table)

    # game loop
    return_menu = False
    while not return_menu:
        screen.fill(white)

        if sudoku.full():
            if sudoku.valid():
                break
            else:
                pass

        button = update_buttons(buttons)

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
                    if event.key in [pygame.K_BACKSPACE, pygame.K_SPACE, pygame.K_DELETE, pygame.K_0, pygame.K_KP0]:
                        erase(sudoku, notes, colors, selected, history)
                    # setting number
                    elif pygame.K_1 <= event.key <= pygame.K_9 or pygame.K_KP1 <= event.key <= pygame.K_KP9:
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            number = event.key - pygame.K_0
                        else:
                            number = event.key - pygame.K_KP1 + 1
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
                    if button is not None:
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
                            if selected is not None and not sudoku.fixed[selected]:
                                erase(sudoku, notes, colors, selected, history)
                            button_pressed = True
                        elif button.id == "copy":
                            pyperclip.copy(code)
                        elif button.id == "back":
                            return_menu = True
                            break
                        elif button.id.count("num_"):
                            if selected is not None and not sudoku.fixed[selected]:
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

        graphical_print(sudoku, notes, colors, current_color_table["light"], selected, grid_shadow)

        draw_buttons(buttons, screen)

        check_quit(events, sudoku= sudoku, notes= notes, colors= colors, history= history, ignore_esc= return_menu)

        pygame.display.update()
        clock.tick(60)

    # fade out after game
    fade(True, 10, sudoku, notes, colors, grid_shadow, buttons, current_color_table)

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
    pos = [width * 3 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Return To Menu",
            small_font,
            "menu",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )
    # copy button
    button_width = 70
    button_height = 50
    pos = [width * 4 / 7 - button_width / 2, height - padding["bottom"] / 2 - button_height / 2]
    size = [button_width, button_height]
    buttons.append(
        Button(
            pos,
            size,
            "dark",
            "white",
            "Copy",
            small_font,
            "copy",
            border_radius= border_radius,
            shadow= create_default_shadow(pos, size, border_radius)
        )
    )

    # overlay and text for win screen
    layer = pygame.surface.Surface((width, height), pygame.SRCALPHA)
    layer.fill(transparent_white)

    text = font.render("Congratulations!", True, black)
    rectangle = text.get_rect(center = (width / 2, padding["top"] / 2))

    # fade in before win screen
    fade(False, 10, sudoku, notes, colors, grid_shadow, buttons, current_color_table, [(text, rectangle)], layer)

    # win screen
    win_screen_loop = True
    while win_screen_loop:
        screen.fill(white)

        graphical_print(sudoku, notes, colors, shadow= grid_shadow)

        screen.blit(layer, (0, 0))
        screen.blit(text, rectangle)

        button = update_buttons(buttons)

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
                    if button is not None:
                        if button.id == "menu":
                            win_screen_loop = False
                            break
                        elif button.id == "copy":
                            pyperclip.copy(code)

        draw_buttons(buttons, screen)

        check_quit(events, sudoku= sudoku, notes= notes, colors= colors, history= history)

        pygame.display.update()
        clock.tick(30)

    # fade out after win screen
    fade(True, 10, sudoku, notes, colors, grid_shadow, buttons, current_color_table, [(text, rectangle)], layer)
