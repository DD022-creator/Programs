def print_solution(board):
    for row in board:
        print(" ".join("Q" if col else "." for col in row))
    print()

def is_safe(board, row, col, n):
    
    for i in range(row):
        if board[i][col]:
            return False

    
    for i, j in zip(range(row - 1, -1, -1), range(col - 1, -1, -1)):
        if board[i][j]:
            return False

    
    for i, j in zip(range(row - 1, -1, -1), range(col + 1, n)):
        if board[i][j]:
            return False

    return True

def solve_n_queens(board, row, n):
    if row == n:
        print_solution(board)
        return True

    res = False
    for col in range(n):
        if is_safe(board, row, col, n):
            board[row][col] = 1
            res = solve_n_queens(board, row + 1, n) or res
            board[row][col] = 0  # Backtrack
    return res

def n_queens(n):
    board = [[0 for _ in range(n)] for _ in range(n)]
    if not solve_n_queens(board, 0, n):
        print("No solution exists.")


try:
    n = int(input("Enter the number of queens (N): "))
    if n <= 0:
        print("Please enter a positive integer greater than 0.")
    else:
        n_queens(n)
except ValueError:
    print("Invalid input! Please enter a valid integer.")
