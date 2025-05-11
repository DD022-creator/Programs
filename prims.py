graph = [
    # A  B  C  D  E
    [ 0, 7, 0, 0, 1],  # A
    [ 7, 0, 3, 0, 8],  # B
    [ 0, 3, 0, 6, 2],  # C
    [ 0, 0, 6, 0, 7],  # D
    [ 1, 8, 2, 7, 0]   # E
]

def prims(graph,s):
    vis = [False] * len(graph)
    vis[s] = True
    t = 0
    while True:
        min = 1000000
        x,y = -1,-1
        for i in range(len(graph)):
            if vis[i]:
                for j in range(len(graph)):
                    if not vis[j] and graph[i][j] != 0 and graph[i][j] < min:
                        min = graph[i][j]
                        x,y = i,j
        if x == -1:
            break
        vis[y] = True
        print(x,"to",y,"=",min)
        t += min
    print("Total cost:",t)

prims(graph,0)