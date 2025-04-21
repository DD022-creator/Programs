import sys

def prims_algorithm(graph, n):
    selected = [False] * n
    selected[0] = True  # Start from the first vertex
    print("Edge : Weight")

    for _ in range(n - 1):
        min_weight = sys.maxsize
        x = y = 0
        for i in range(n):
            if selected[i]:
                for j in range(n):
                    if not selected[j] and graph[i][j]:
                        if min_weight > graph[i][j]:
                            min_weight = graph[i][j]
                            x, y = i, j
        print(f"{x} - {y} : {graph[x][y]}")
        selected[y] = True

def main():
    n = int(input("Enter the number of vertices: "))
    print("Enter the cost matrix (use 0 if no edge):")
    graph = []
    for i in range(n):
        row = list(map(int, input(f"Row {i}: ").split()))
        graph.append(row)

    prims_algorithm(graph, n)

if __name__ == "__main__":
    main()
