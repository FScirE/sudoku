import random
import copy
import threading
m = threading.Lock()

def generate_board(end = 0):
    print("Generating solved sukodu...")
    board = [{"value": 0, "fixed": False} for _ in range(81)]
    row = 0
    stuck_row = 0
    stuck_counter = 0   
    while not full_board(board):       
        try:
            for i in range(9):
                # set cell to random from available
                available = get_available(board, row * 9 + i)
                board[row * 9 + i]["value"] = random.choice(available)
                board[row * 9 + i]["fixed"] = True
            row += 1          
            if row - stuck_row >= 2:
                stuck_row = row
            else:
                stuck_counter += 1
            if stuck_counter > 100:
                # start over if stuck
                board = [{"value": 0, "fixed": False} for _ in range(81)]
                row = 0
                stuck_row = 0
                stuck_counter = 0              
        except:
            # out of options, go back one row
            for i in range(9):
                board[row * 9 + i]["value"] = 0
                board[row * 9 + i]["fixed"] = False
            row -= 1
    remaining = [i for i in range(81)]
    print("Removing numbers...")
    while len(remaining) > end:    
        print(f"{len(remaining)} / {81 - end} remain ", end="\r")
        options = []
        threads = []
        # start threads looking for values to remove
        if len(remaining) > 32:
            amt_threads = 1
        elif len(remaining) > 16:
            amt_threads = 16
        else:
            amt_threads = len(remaining)
        for i in range(amt_threads):
            t = threading.Thread(target=thread_work, args=(copy.deepcopy(board), remaining, options,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        # if options exist to remove, remove first
        if options:
            remove = options[0]
            board[remove]["value"] = 0
            board[remove]["fixed"] = False
            remaining.remove(remove)
    print("\r              ")
    return board

def thread_work(board, remaining, options):
    # get random index
    m.acquire()
    index = random.choice(remaining)
    remaining.remove(index)
    m.release()
    # remove cell value
    board[index]["value"] = 0
    solutions = solve_board(board)
    # only one solution -> can only be removed by main thread
    if len(solutions) <= 1:
        m.acquire()
        remaining.append(index)
        options.append(index)
        m.release()
    
def solve_board(board, limit = 2, solutions = None):
    if solutions is None:
        solutions = []
    if full_board(board):
        solutions.append(board)
        return solutions
    # get first empty cell
    try:
        index = next(i for i, c in enumerate(board) if c["value"] == 0)
    except:
        return []
    # try all possible numbers
    for val in get_available(board, index):
        board[index]["value"] = val
        solutions = solve_board(copy.deepcopy(board), limit, solutions)
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
    for i in range(len(board)):
        value = board[i]["value"]
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
        if idx_row != index and board[idx_row]["value"] == value:
            return True
        elif idx_col != index and board[idx_col]["value"] == value:
            return True  
        elif idx_block != index and board[idx_block]["value"] == value:
            return True       
    return False

def full_board(board):
    return all(map(lambda c: c["value"] != 0, board))

def print_board(board: list[object]):
    section = ""
    for i in range(len(board)):
        value = board[i]["value"]
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

board = generate_board()

# for i in range(0, 27):
#     board[i]["value"] = 0
# solutions = solve_board(copy.deepcopy(board), 2)
# print(len(solutions))

print_board(board)

# print(valid_board(board))
