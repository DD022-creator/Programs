def print_matrix(matrix):
    for row in matrix:
        print(" ".join(map(str, row)))
    print()

def warshall_algorithm(graph):
    n = len(graph)
    print("Initial Adjacency Matrix:")
    print_matrix(graph)

    for i in range(n):
        print(f"After including vertex {i + 1} as intermediate:")
        for j in range(n):
            for k in range(n):
                if i==j:
                    graph[i][j]=0
                else:
                    graph[i][j] = graph[i][j] or (graph[i][k] and graph[k][j])
        print_matrix(graph)
    return graph

def main():
    n = int(input("Enter the number of vertices: "))
    print("Enter the adjacency matrix (row by row, space-separated):")
    graph = []
    for i in range(n):
        row = list(map(int, input(f"Row {i + 1}: ").split()))
        graph.append(row)

    warshall_algorithm(graph)

if __name__ == "__main__":
    main()
