import random

def generate_board(end = 0):
    # generate a solved sudoku
    print("Generating solved sukodu...")
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

def print_board(board: list[object]):
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

board, fixed = generate_board()

# for i in range(0, 27):
#     board[i]["value"] = 0
# solutions = solve_board(board[:], 2)
# print(len(solutions))

print_board(board)

# print(valid_board(board))
