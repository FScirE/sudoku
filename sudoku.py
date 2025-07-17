import random
import pygame

# pygame setup
pygame.init()
pygame.display.set_caption("Sudoku")
width = 800
height = 800
screen = pygame.display.set_mode(size=(width, height))
clock = pygame.time.Clock()

padding = 100
font_size = 32
font = pygame.font.SysFont("arial", font_size)

white = (255, 255, 255)
light_blue = (210, 250, 255)
dark_blue = (0, 90, 180)
black = (0, 0, 0)

screen.fill(white)

#sudoku functions -------------------------

def generate_board(end = 0, graphics = True):
    # generate a solved sudoku

    print("Generating solved sukodu...")
    if graphics:
        text = font.render("Generating solved sudoku...", True, black, white)
        rectangle = text.get_rect()
        rectangle.center = (width // 2, height // 2)
        screen.blit(text, rectangle)
        pygame.display.update()

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
    # remove numbers randomly until limit for how many numbers to check is reached
    remaining = [i for i in range(81)]
    print("Removing numbers...")
    while len(remaining) > end:

        print(f"{len(remaining)} / {81 - end} remain ", end="\r")
        if graphics:
            screen.fill(white)
            text_g = font.render("Solved sudoku generated", True, black)
            text_r = font.render("Removing numbers...", True, black)
            text_p = font.render(f"{len(remaining)} / {81 - end} remain", True, black)
            rectangle_g = text_g.get_rect(center = (width // 2, height // 2 - (font_size + 4)))
            rectangle_r = text_r.get_rect(center = (width // 2, height // 2))
            rectangle_p = text_p.get_rect(center = (width // 2, height // 2 + (font_size + 4)))
            screen.blit(text_g, rectangle_g)
            screen.blit(text_r, rectangle_r)
            screen.blit(text_p, rectangle_p)
            pygame.display.update()

        remove = random.choice(remaining)
        remaining.remove(remove)
        old_value = board[remove]
        board[remove] = 0
        if (len(solve_board(board[:])) > 1):
            # board value cant be removed
            board[remove] = old_value
        else:
            # finish removing value
            fixed[remove] = 0
    print("\r              ")
    return board, fixed

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

def print_board(board, graphics = True, hover = None):
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
            if hover is not None and i == hover:
                rect = pygame.rect.Rect(
                    (i % 9) * cell_w + padding,
                    (i // 9) * cell_h + padding,
                    cell_w,
                    cell_h
                )
                pygame.draw.rect(screen, light_blue, rect)
            value = board[i]
            if value == 0:
                continue
            text = font.render(f"{value}", True, black)
            rectangle = text.get_rect(center = (
                (i % 9 + 0.5) * cell_w + padding,
                (i // 9 + 0.5) * cell_h + padding
            ))
            screen.blit(text, rectangle)
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

# -------------------------

# sudoku setup
board, fixed = generate_board()
print_board(board, False)

# game loop
while True:
    screen.fill(white)

    mouse = pygame.mouse.get_pos()
    m_x = mouse[0]
    m_y = mouse[1]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()

    hover = None
    if m_x > padding and m_x < width - padding and m_y > padding and m_y < height - padding:
        row = ((m_y - padding) * 9) // (height - padding * 2)
        col = ((m_x - padding) * 9) // (width - padding * 2)
        hover = row * 9 + col

    print_board(board, hover=hover)

    pygame.display.update()
    clock.tick(60)
