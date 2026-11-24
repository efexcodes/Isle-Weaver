from collections import deque

from .union_find import UnionFind


def kruskal_mst(edges, n):
    uf = UnionFind(n)
    mst = []
    for e in sorted(edges, key=lambda e: e.weight):
        if len(mst) == n - 1:
            break
        if uf.union(e.a, e.b):
            mst.append(e)
    return mst


def bfs_connected(edges, n):
    if n <= 1:
        return True
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e.a].append(e.b)
        adj[e.b].append(e.a)

    seen = [False] * n
    seen[0] = True
    queue = deque([0])
    reached = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                reached += 1
                queue.append(v)
    return reached == n
