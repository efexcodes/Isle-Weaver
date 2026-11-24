import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.algorithms import kruskal_mst, prim_mst
from core.graph import Bridge
from game.level_generator import LEVELS, generate_level

REPEATS = 5


def random_graph(rng, n, density):
    edges = [Bridge(i, i + 1, rng.randint(1, 1000)) for i in range(n - 1)]
    for i in range(n):
        for j in range(i + 2, n):
            if rng.random() < density:
                edges.append(Bridge(i, j, rng.randint(1, 1000)))
    return edges


def best_time(fn, edges, n):
    best = float("inf")
    for _ in range(REPEATS):
        start = time.perf_counter()
        fn(edges, n)
        best = min(best, time.perf_counter() - start)
    return best * 1000


def run_random(sizes, density, label):
    rng = random.Random(7)
    print(f"\n{label}")
    print(f"{'V':>6} {'E':>8} {'Kruskal (ms)':>14} {'Prim (ms)':>12} {'sama?':>7}")
    for n in sizes:
        edges = random_graph(rng, n, density)
        k = best_time(kruskal_mst, edges, n)
        p = best_time(prim_mst, edges, n)
        same = sum(e.weight for e in kruskal_mst(edges, n)) == sum(e.weight for e in prim_mst(edges, n))
        print(f"{n:>6} {len(edges):>8} {k:>14.3f} {p:>12.3f} {'ya' if same else 'TIDAK':>7}")


def run_levels():
    print("\nGraf level di dalam game (rata-rata 50 peta per level)")
    print(f"{'Level':>6} {'V':>4} {'E rata2':>8} {'Kruskal (us)':>13} {'Prim (us)':>11}")
    for i, cfg in enumerate(LEVELS):
        rng = random.Random(i)
        maps = [generate_level(i, 920, 474, rng) for _ in range(50)]
        n = cfg["islands"]
        e_avg = sum(len(m.edges) for m in maps) / len(maps)
        k = sum(best_time(kruskal_mst, m.edges, n) for m in maps) / len(maps) * 1000
        p = sum(best_time(prim_mst, m.edges, n) for m in maps) / len(maps) * 1000
        print(f"{i + 1:>6} {n:>4} {e_avg:>8.1f} {k:>13.1f} {p:>11.1f}")


if __name__ == "__main__":
    run_levels()
    run_random([100, 200, 400, 800, 1600], 0.02, "Graf jarang (kepadatan 2%)")
    run_random([100, 200, 400, 800, 1600], 0.5, "Graf padat (kepadatan 50%)")
