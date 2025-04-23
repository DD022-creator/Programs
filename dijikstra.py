import sys

def dijkstra(graph, src):
    n = len(graph)
    dist = [sys.maxsize] * n  # Distance from source to each vertex
    dist[src] = 0
    visited = [False] * n

    for _ in range(n):
        # Find the unvisited vertex with the smallest distance
        min_dist = sys.maxsize
        u = -1
        for i in range(n):
            if not visited[i] and dist[i] < min_dist:
                min_dist = dist[i]
                u = i

        visited[u] = True

        # Update distances of adjacent vertices
        for v in range(n):
            if graph[u][v] > 0 and not visited[v]:
                if dist[u] + graph[u][v] < dist[v]:
                    dist[v] = dist[u] + graph[u][v]

    # Print result
    print("Vertex\tDistance from Source")
    for i in range(n):
        print(f"{i}\t{dist[i]}")

# ----- User Input -----
print("Dijkstra's Algorithm")
n = int(input("Enter the number of vertices: "))

print(f"Enter the adjacency matrix (enter 0 if no edge exists):")
graph = []
for i in range(n):
    row = list(map(int, input(f"Row {i}: ").split()))
    graph.append(row)

src = int(input("Enter the source vertex (0 to n-1): "))
dijkstra(graph, src)
