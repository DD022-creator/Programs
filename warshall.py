graph = [
    # 1  2  3  4  5  6
    [ 0, 4, 0, 0, 0, 0],  # 1
    [ 0, 0, 0, 4, 0, 0],  # 2
    [ 0, 3, 0, 0, 0, 0],  # 3
    [ 0, 0, 2, 0, 3, 0],  # 4
    [ 0, 4, 0, 5, 0, 1],  # 5
    [ 5, 0, 0, 0, 0, 0]   # 6
]

def floyd(graph):
    for k in range(len(graph)):
        for i in range(len(graph)):
            for j in range(len(graph)):
                graph[i][j] = graph[i][j] or (graph[i][k] and graph[k][j])
    print("Shortest path between all nodes:")
    for i in range(len(graph)):
        for j in range(len(graph)):
            print(graph[i][j]!=0,end = "  ")
        print()
floyd(graph)