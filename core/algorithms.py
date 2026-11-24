import heapq
from collections import deque
from itertools import count

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


def prim_mst(edges, n, start=0):
    if n == 0:
        return []
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e.a].append((e.b, e))
        adj[e.b].append((e.a, e))

    tie = count()
    visited = [False] * n
    visited[start] = True
    heap = [(e.weight, next(tie), v, e) for v, e in adj[start]]
    heapq.heapify(heap)
    mst = []
    while heap and len(mst) < n - 1:
        _, _, v, e = heapq.heappop(heap)
        if visited[v]:
            continue
        visited[v] = True
        mst.append(e)
        for u, f in adj[v]:
            if not visited[u]:
                heapq.heappush(heap, (f.weight, next(tie), u, f))
    return mst


def connected_groups(edges, n):
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e.a].append(e.b)
        adj[e.b].append(e.a)

    seen = [False] * n
    groups = 0
    for s in range(n):
        if seen[s]:
            continue
        groups += 1
        seen[s] = True
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    queue.append(v)
    return groups


def bfs_connected(edges, n):
    return connected_groups(edges, n) <= 1
