import random
import threading
import os

#sudoku class ----------------------------

class Sudoku:
    def __init__(self):
        self.mutex = threading.Lock()
        self.atomic_lock = threading.Lock()
        self.atomic_counter = 0

        self.board = [0] * 81
        self.fixed = [True] * 81

    def generate_completed_board(self):
        # generate a solved sudoku
        row = 0
        stuck_row = 0
        stuck_counter = 0
        while not full_board(self.board):
            try:
                for i in range(9):
                    # set cell to random from available
                    available = get_available(self.board, row * 9 + i)
                    self.board[row * 9 + i] = random.choice(available)
                row += 1
                if row - stuck_row >= 2:
                    stuck_row = row
                else:
                    stuck_counter += 1
                if stuck_counter > 100:
                    # start over if stuck
                    self.board = [0] * 81
                    row = 0
                    stuck_row = 0
                    stuck_counter = 0
            except:
                # out of options, go back one row
                for i in range(9):
                    self.board[row * 9 + i] = 0
                row -= 1
        return self.board, self.fixed

    def remove_board_numbers(self, end = 0, multithread = True, quit_signal = None):
        # remove numbers randomly until limit for how many numbers to check is reached
        remaining = [i for i in range(81)]
        random.shuffle(remaining)
        while len(remaining) > end:
            if quit_signal is not None and quit_signal.is_set():
                return None, None
            self.atomic_lock.acquire()
            self.atomic_counter = len(remaining) - end
            self.atomic_lock.release()
            if multithread:
                threads = []
                options = []
                # start looking for multiple values to remove simultaneously
                thread_limit = os.cpu_count()
                if thread_limit > 8:
                    thread_limit = 8
                num_remaining = len(remaining)
                if num_remaining > 32:
                    num_threads = 1
                elif num_remaining > thread_limit:
                    num_threads = thread_limit
                else:
                    num_threads = num_remaining
                for _ in range(num_threads):
                    t = threading.Thread(target=thread_work, args=(self.board[:], remaining, options, self.mutex,))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
                # remove first option
                if options:
                    remove = options[0]
                    self.board[remove] = 0
                    self.fixed[remove] = False
                    remaining.remove(remove)
            else:
                remove = random.choice(remaining)
                remaining.remove(remove)
                old_value = self.board[remove]
                self.board[remove] = 0
                if (len(solve_board(self.board[:])) > 1):
                    # board value cant be removed
                    self.board[remove] = old_value
                else:
                    # finish removing value
                    self.fixed[remove] = False
        return self.board, self.fixed

    def valid(self):
        return valid_board(self.board)

    def full(self):
        return full_board(self.board)

    def print(self):
        return print_board(self.board)

    def to_string(self):
        # row based string
        str_r = "r"
        zero_r = 0
        for r in range(9):
            for c in range(9):
                index = r * 9 + c
                if self.fixed[index]:
                    value_r = self.board[index]
                else:
                    value_r = 0
                if value_r == 0:
                    zero_r += 1
                    if c < 8 or r < 8:
                        continue
                if zero_r > 2:
                    str_r += f"{hex(zero_r)}"
                else:
                    str_r += "0" * zero_r
                if value_r != 0:
                    zero_r = 0
                    str_r += str(value_r)
        # column based string
        str_c = "c"
        zero_c = 0
        for c in range(9):
            for r in range(9):
                index = r * 9 + c
                if self.fixed[index]:
                    value_c = self.board[index]
                else:
                    value_c = 0
                if value_c == 0:
                    zero_c += 1
                    if c < 8 or r < 8:
                        continue
                if zero_c > 2:
                    str_c += f"{hex(zero_c)}"
                else:
                    str_c += "0" * zero_c
                if value_c != 0:
                    zero_c = 0
                    str_c += str(value_c)
        # return shortest option
        return str_r if len(str_r) <= len(str_c) else str_c

    def from_string(self, string):
        board = [0] * 81
        fixed = [False] * 81
        if not string:
            return False
        direction = string[0]
        # not valid direction
        if direction not in ["r", "c"]:
            return False
        i = 1
        counter = 0
        while i < len(string):
            # too many cells
            if counter >= 81:
                return False
            # invalid symbol
            if not string[i].isnumeric():
                return False
            if string[i] != "0":
                if direction == "r":
                    # row direction
                    board[counter] = int(string[i])
                    fixed[counter] = True
                else:
                    # column direction
                    board[(counter * 9 + counter // 9) % 81] = int(string[i])
                    fixed[(counter * 9 + counter // 9) % 81] = True
            elif i < len(string) - 1 and string[i + 1] == "x":
                if string[i + 2] not in ["1", "2"]:
                    counter += int(string[i:i+3], base=0)
                    i += 3
                else:
                    # >=16 zeros in a row
                    counter += int(string[i:i+4], base=0)
                    i += 4
                continue
            i += 1
            counter += 1
        # incorrect number of cells
        if counter != 81:
            return False
        # invalid board
        if not valid_board(board) or len(solve_board(board[:])) != 1:
            return False
        # set board if valid
        self.board = board
        self.fixed = fixed
        return True

    def solve(self):
        self.board = solve_board(self.board[:], 1)[0]

#sudoku functions -------------------------

def solve_board(board, limit = 2, solutions = None):
    if solutions is None:
        solutions = []
    if full_board(board):
        solutions.append(board)
        return solutions
    # get empty cell with least amount of options
    index = -1
    min_amt = 10
    for i in range(81):
        if board[i] != 0:
            continue
        amt_options = len(get_available(board, i))
        if amt_options == 0:
            return solutions
        if amt_options < min_amt:
            min_amt = amt_options
            index = i
            if amt_options == 1:
                break
    # index = board.index(0)
    # try all possible numbers
    for val in get_available_smart(board, index):
        board[index] = val
        solutions = solve_board(board[:], limit, solutions)
        if len(solutions) >= limit:
            break
    return solutions

def thread_work(board, remaining, options, mutex):
    # get index
    mutex.acquire()
    index = remaining.pop()
    mutex.release()
    # remove cell value
    board[index] = 0
    # one solution -> to be added to list of possible removals for main thread
    if len(solve_board(board)) <= 1:
        mutex.acquire()
        remaining.append(index)
        options.append(index)
        mutex.release()

# old available function
def get_available(board, index):
    available = []
    for i in range(9):
        val = i + 1
        if not conflicts(board, index, val):
            available.append(val)
    return available
# newer smarted available function
def get_available_smart(board, index):
    available = []
    if board[index]:
        return [board[index]]
    row = index // 9
    col = index % 9
    for i in range(9):
        val = i + 1
        conflict = conflicts(board, index, val)
        if conflict:
            continue
        else:
            other_r = False
            other_c = False
            for r in range(9):
                index_r = row * 9 + r
                index_c = r * 9 + col
                if (not board[index_r] and
                    index_r != index and
                    not other_r and
                    not conflicts(board, index_r, val)):
                    other_r = True
                if (not board[index_c] and
                    index_c != index and
                    not other_c and
                    not conflicts(board, index_c, val)):
                    other_c = True
            if not other_r or not other_c:
                return [val]
            available.append(val)
    return available
# new available function for fine printing
def get_available_analysis(board, index):
    available = []
    messages = []
    if board[index]:
        return [board[index]], [f"'{board[index]}' is this cell's assigned value"]
    row = index // 9
    col = index % 9
    for i in range(9):
        val = i + 1
        conflict = conflicts(board, index, val)
        if conflict == 1:
            messages.append(f"'{val}' is already present in row")
        elif conflict == 2:
            messages.append(f"'{val}' is already present in column")
        elif conflict == 3:
            messages.append(f"'{val}' is already present in box")
        else:
            other_r = False
            other_c = False
            for r in range(9):
                index_r = row * 9 + r
                index_c = r * 9 + col
                if (not board[index_r] and
                    index_r != index and
                    not other_r and
                    not conflicts(board, index_r, val)):
                    other_r = True
                if (not board[index_c] and
                    index_c != index and
                    not other_c and
                    not conflicts(board, index_c, val)):
                    other_c = True
            if not other_r:
                return [val], [f"For this row, '{val}' must be in this cell"]
            if not other_c:
                return [val], [f"For this column, '{val}' must be in this cell"]
            available.append(val)
    messages.sort(key=lambda k: k.split(" ")[-1])
    return available, messages

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
            return 1
        elif idx_col != index and board[idx_col] == value:
            return 2
        elif idx_block != index and board[idx_block] == value:
            return 3
    return 0

def full_board(board):
    return all(map(lambda c: c != 0, board))

def print_board(board):
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
