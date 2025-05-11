graph = [
    # A  B  C  D  E
    [ 0, 7, 0, 0, 1],  # A
    [ 7, 0, 3, 0, 8],  # B
    [ 0, 3, 0, 6, 2],  # C
    [ 0, 0, 6, 0, 7],  # D
    [ 1, 8, 2, 7, 0]   # E
]

def find(v,d):
    m = 1000000
    mi = -1
    for i in range(len(v)):
        if not v[i] and d[i] < m:
            m = d[i]
            mi = i
    return mi

def dig(g,s):
    vis = [False] * len(g)
    prev = [False] * len(g)
    dist = [1000000] * len(g)
    dist[s] = 0
    for i in range(len(g)):
        cur = find(vis,dist)
        vis[cur] = True
        for j in range(len(g)):
            if  g[cur][j] != 0 and dist[cur] + g[cur][j] < dist[j]:
                dist[j] = dist[cur] + g[cur][j]
                prev[j] = cur

    print("Shortest path from",s,"to all other nodes:")
    for i in range(len(g)):
        print(s,"to",i,"=",dist[i],"   prev:",prev[i])

dig(graph,0)