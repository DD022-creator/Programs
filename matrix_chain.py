import sys

def matrix_chain_order(p):
    n = len(p) - 1  # Number of matrices
    m = [[0 for _ in range(n)] for _ in range(n)]
    s = [[0 for _ in range(n)] for _ in range(n)]  # To store split points

    for L in range(2, n + 1):  # L is chain length
        for i in range(n - L + 1):
            j = i + L - 1
            m[i][j] = sys.maxsize
            for k in range(i, j):
                cost = m[i][k] + m[k+1][j] + p[i] * p[k+1] * p[j+1]
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k  # Store k for optimal split

    return m, s

def print_optimal_parens(s, i, j):
    if i == j:
        return f"A{i+1}"
    else:
        return "(" + print_optimal_parens(s, i, s[i][j]) + " x " + print_optimal_parens(s, s[i][j]+1, j) + ")"

# Get input from user
print("Matrix Chain Multiplication")
print("Enter the dimensions of matrices as space-separated values.")
print("For example, for matrices A(10x20), B(20x30), C(30x40), enter: 10 20 30 40")

dims_input = input("Enter dimensions: ")

# Convert input to a list of integers
try:
    p = list(map(int, dims_input.strip().split()))
    if len(p) < 2:
        print("You need at least two numbers (one matrix).")
    else:
        m, s = matrix_chain_order(p)
        n = len(p) - 1
        print("\nMinimum number of multiplications is:", m[0][n-1])
        print("Optimal multiplication order is:", print_optimal_parens(s, 0, n-1))
        print("Final resulting matrix dimension is: ({} x {})".format(p[0], p[-1]))
except ValueError:
    print("Invalid input. Please enter only integers separated by spaces.")
