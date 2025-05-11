graph = [
    # 1  2  3  4  5  6
    [ 100000, 4, 100000, 100000, 100000, 100000],  # 1
    [ 100000, 100000, 100000, 4, 100000, 100000],  # 2
    [ 100000, 3, 100000, 100000, 100000, 100000],  # 3
    [ 100000, 100000, 2, 100000, 3, 100000],  # 4
    [ 100000, 4, 100000, 5, 100000, 1],  # 5
    [ 5, 100000, 100000, 100000, 100000, 100000]   # 6
]

def floyd(graph):
    for k in range(len(graph)):
        for i in range(len(graph)):
            for j in range(len(graph)):
                graph[i][j] = min(graph[i][j],graph[i][k] + graph[k][j])
    print("Shortest path between all nodes:")
    for i in range(len(graph)):
        for j in range(len(graph)):
            print(graph[i][j],end = "  ")
        print()
floyd(graph)