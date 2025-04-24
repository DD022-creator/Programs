def floyd_warshall(graph):
    V = len(graph)
    dist = [row[:] for row in graph]  # Deep copy of the graph

    print("\nInitial matrix:")
    print_matrix(dist)

    # Applying Floyd-Warshall with step-by-step output
    for k in range(V):
        print(f"\nAfter considering vertex {k + 1} as intermediate:")
        for i in range(V):
            for j in range(V):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
        print_matrix(dist)

    return dist

# Helper function to print the matrix nicely
def print_matrix(matrix):
    for row in matrix:
        print(' '.join(['inf' if x == float('inf') else str(x) for x in row]))

# Get the adjacency matrix from the user
def get_matrix():
    V = int(input("Enter the number of vertices: "))
    print("Enter the adjacency matrix (use 'inf' for infinity):")
    graph = []

    for i in range(V):
        row = input(f"Row {i+1}: ").split()
        row = [float('inf') if x == 'inf' else int(x) for x in row]
        graph.append(row)
    
    return graph

# Main function
def main():
    graph = get_matrix()
    result = floyd_warshall(graph)

    print("\nFinal shortest distances between every pair of vertices:")
    print_matrix(result)

if __name__ == "__main__":
    main()
