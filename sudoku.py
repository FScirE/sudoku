import sys
import random
import copy
import threading
import pygame
mutex = threading.Lock()
atomic_lock = threading.Lock()
atomic_counter = 0

# pygame setup
pygame.init()
pygame.display.set_caption("Sudoku")
width = 800
height = 800
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

padding = 100
note_padding = 4
font_size = 32
font = pygame.font.SysFont("arial", font_size)
small_font = pygame.font.SysFont("arial", font_size // 2)

transparent_white = (255, 255, 255, 128)
white = (255, 255, 255)
light_blue = (230, 245, 255)
medium_blue = (105, 160, 210)
dark_blue = (0, 90, 180)
black = (0, 0, 0)

screen.fill(white)

#sudoku functions -------------------------

def generate_completed_board():
    # generate a solved sudoku
    board = [0] * 81
    fixed = [True] * 81
    row = 0
    stuck_row = 0
    stuck_counter = 0
    while not full_board(board):
        try:
            for i in range(9):
                # set cell to random from available
                available = get_available(board, row * 9 + i)
                board[row * 9 + i] = random.choice(available)
            row += 1
            if row - stuck_row >= 2:
                stuck_row = row
            else:
                stuck_counter += 1
            if stuck_counter > 100:
                # start over if stuck
                board = [0] * 81
                row = 0
                stuck_row = 0
                stuck_counter = 0
        except:
            # out of options, go back one row
            for i in range(9):
                board[row * 9 + i] = 0
            row -= 1
    return board, fixed

def remove_board_numbers(board, fixed, end = 0, multithread = True):
    global atomic_counter
    # remove numbers randomly until limit for how many numbers to check is reached
    remaining = [i for i in range(81)]
    while len(remaining) > end:
        atomic_lock.acquire()
        atomic_counter = len(remaining) - end
        atomic_lock.release()
        if multithread:
            threads = []
            options = []
            # start looking for multiple values to remove simultaneously
            num_remaining = len(remaining)
            if num_remaining > 36:
                num_threads = 1
            elif num_remaining > 16:
                num_threads = 16
            else:
                num_threads = num_remaining
            for _ in range(num_threads):
                t = threading.Thread(target=thread_work, args=(board[:], remaining, options,))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            # remove first option
            if options:
                remove = options[0]
                board[remove] = 0
                fixed[remove] = False
                remaining.remove(remove)
        else:
            remove = random.choice(remaining)
            remaining.remove(remove)
            old_value = board[remove]
            board[remove] = 0
            if (len(solve_board(board[:])) > 1):
                # board value cant be removed
                board[remove] = old_value
            else:
                # finish removing value
                fixed[remove] = False

def thread_work(board, remaining, options):
    # get random index
    mutex.acquire()
    index = random.choice(remaining)
    remaining.remove(index)
    mutex.release()
    # remove cell value
    board[index] = 0
    # one solution -> to be added to list of possible removals for main thread
    if len(solve_board(board)) <= 1:
        mutex.acquire()
        remaining.append(index)
        options.append(index)
        mutex.release()

def solve_board(board, limit = 2, solutions = None):
    if solutions is None:
        solutions = []
    if full_board(board):
        solutions.append(board)
        return solutions
    # get first empty cell
    try:
        index = board.index(0)
    except:
        return []
    # try all possible numbers
    for val in get_available(board, index):
        board[index] = val
        solutions = solve_board(board[:], limit, solutions)
        if len(solutions) >= limit:
            break
    return solutions

def get_available(board, index):
    available = []
    for i in range(9):
        val = i + 1
        if not conflicts(board, index, val):
            available.append(val)
    return available

def valid_board(board):
    for i in range(81):
        value = board[i]
        if value == 0:
            continue
        if conflicts(board, i, value):
            return False
    return True

def conflicts(board, index, value):
    row = index // 9
    col = index % 9
    for j in range(9):
        idx_row = row * 9 + j
        idx_col = col + 9 * j
        idx_block = ((row // 3) * 3 + j // 3) * 9 + (col // 3) * 3 + j % 3
        if idx_row != index and board[idx_row] == value:
            return True
        elif idx_col != index and board[idx_col] == value:
            return True
        elif idx_block != index and board[idx_block] == value:
            return True
    return False

def full_board(board):
    return all(map(lambda c: c != 0, board))

def print_board(board, fixed, notes, graphics = True, hover = None):
    if not graphics:
        section = ""
        for i in range(81):
            value = board[i]
            value = value if value != 0 else "."
            section += f"{value} "
            if (i + 1) % 3 == 0 and (i + 1) % 9 != 0:
                section += "|"
            if i % (3 * 9) == 0 and i > 0:
                print("--------" + "+---------" * 2)
            if (i + 1) % 9 == 0:
                print(section)
                section = ""
            else:
                section += " "
    else:
        for i in range(81):
            cell_w = (width - padding * 2) / 9
            cell_h = (height - padding * 2) / 9
            # draw hover marking
            if hover is not None and i == hover:
                rect = pygame.rect.Rect(
                    (i % 9) * cell_w + padding,
                    (i // 9) * cell_h + padding,
                    cell_w,
                    cell_h
                )
                pygame.draw.rect(screen, light_blue, rect)
            # draw notes
            cell_notes = notes[i]
            for note in cell_notes:
                note_col = (note - 1) % 3
                note_row = (note - 1) // 3
                text = small_font.render(f"{note}", True, medium_blue)
                rectangle = text.get_rect(center = (
                    (i % 9 + 0.5) * cell_w + padding + (note_col - 1) * (cell_w - note_padding * 2) // 3,
                    (i // 9 + 0.5) * cell_h + padding + (1 - note_row) * (cell_h - note_padding * 2) // 3
                ))
                screen.blit(text, rectangle)
            # draw cell values
            value = board[i]
            color = black if fixed[i] else dark_blue
            if value == 0:
                continue
            text = font.render(f"{value}", True, color)
            rectangle = text.get_rect(center = (
                (i % 9 + 0.5) * cell_w + padding,
                (i // 9 + 0.5) * cell_h + padding
            ))
            screen.blit(text, rectangle)
        # draw grid
        for i in range(10):
            if i % 3 == 0:
                line_width = 3
            else:
                line_width = 1
            pygame.draw.line(screen, black,
                             (i * (width - padding * 2) / 9 + padding, padding),
                             (i * (width - padding * 2) / 9 + padding, height - padding), line_width)
            pygame.draw.line(screen, black,
                             (padding, i * (height - padding * 2) / 9 + padding),
                             (width - padding, i * (height - padding * 2) / 9 + padding), line_width)

def check_quit(threads = None):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            if threads:
                screen.fill(white)
                text = font.render("Closing...", True, black)
                rectangle = text.get_rect(center = (width // 2, height // 2))
                screen.blit(text, rectangle)
                pygame.display.update()
                for t in threads:
                    t.join()
            pygame.quit()
            sys.exit()

# -------------------------

# sudoku setup
print("Generating completed board...")
board, fixed = generate_completed_board()

print("Removing numbers...")
thread = threading.Thread(target=remove_board_numbers, args=(board, fixed,))
thread.start()
while thread.is_alive():
    screen.fill(white)

    text_g = font.render("Solved sudoku generated", True, black)
    text_r = font.render("Removing numbers...", True, black)
    atomic_lock.acquire()
    print(f"Remaining: {atomic_counter} ", end="\r")
    text_p = font.render(f"Remaining: {atomic_counter}", True, black)
    atomic_lock.release()
    rectangle_g = text_g.get_rect(center = (width // 2, height // 2 - (font_size + 4)))
    rectangle_r = text_r.get_rect(center = (width // 2, height // 2))
    rectangle_p = text_p.get_rect(center = (width // 2, height // 2 + (font_size + 4)))
    screen.blit(text_g, rectangle_g)
    screen.blit(text_r, rectangle_r)
    screen.blit(text_p, rectangle_p)

    check_quit([thread])

    pygame.display.update()
    clock.tick(30)
print("\r             ")

notes = [[] for _ in range(81)]
print_board(board, fixed, notes, False)
history = []

# game loop
filled = False
correct = False
while True:
    screen.fill(white)

    filled = full_board(board)
    correct = valid_board(board)

    if filled:
        if correct:
            break
        else:
            pass

    mouse = pygame.mouse.get_pos()
    m_x = mouse[0]
    m_y = mouse[1]

    hover = None
    if m_x > padding and m_x < width - padding and m_y > padding and m_y < height - padding:
        row = ((m_y - padding) * 9) // (height - padding * 2)
        col = ((m_x - padding) * 9) // (width - padding * 2)
        hover = row * 9 + col

    for event in pygame.event.get(exclude=pygame.QUIT):
        # add event back in queue for future event get
        pygame.event.post(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
                if history:
                    popped = history.pop()
                    board = popped[0]
                    notes = popped[1]
                continue
            if hover is not None and not fixed[hover]:
                board_old = board[:]
                notes_old = copy.deepcopy(notes)
                # ereasing
                if event.key in [pygame.K_BACKSPACE, pygame.K_SPACE, pygame.K_0, pygame.K_KP0]:
                    board[hover] = 0
                    notes[hover] = []
                # setting number
                elif pygame.K_0 <= event.key <= pygame.K_9 or pygame.K_KP0 <= event.key <= pygame.K_KP9:
                    if pygame.K_0 <= event.key <= pygame.K_9:
                        number = event.key - pygame.K_0
                    else:
                        number = event.key - pygame.K_KP0
                    if event.mod & pygame.KMOD_SHIFT:
                        # add note
                        if number not in notes[hover]:
                            notes[hover].append(number)
                        # remove note
                        else:
                            notes[hover].remove(number)
                    elif board[hover] != number:
                        board[hover] = number
                        notes[hover] = []
                else:
                    continue
                # add to history
                if board == board_old and notes == notes_old:
                    pass
                elif history and board == history[-1][0] and notes == history[-1][1]:
                    history.pop()
                else:
                    history.append((board_old, notes_old))

    print_board(board, fixed, notes, hover=hover)

    check_quit()

    pygame.display.update()
    clock.tick(60)

# win screen
while True:
    screen.fill(white)

    print_board(board, fixed, notes)

    layer = pygame.surface.Surface((width, height), pygame.SRCALPHA)
    layer.fill(transparent_white)
    screen.blit(layer, (0, 0))

    text = font.render("Congratulations!", True, black, white)
    rectangle = text.get_rect(center = (width // 2, padding // 2))
    screen.blit(text, rectangle)

    check_quit()

    pygame.display.update()
    clock.tick(30)
