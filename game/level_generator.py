import math
import random
from dataclasses import dataclass

from core.algorithms import kruskal_mst
from core.geometry import distance, segment_distance
from core.graph import Bridge, Island
from core.union_find import UnionFind

LEVELS = [
    {"name": "Gugus Pemula", "islands": 6, "k": 3},
    {"name": "Selat Kembar", "islands": 8, "k": 3},
    {"name": "Teluk Sunyi", "islands": 10, "k": 3},
]

MARGIN = 58
MIN_GAP = 78
CLEARANCE = 30
COST_SCALE = 5
BUDGET_SLACK = 1.4


@dataclass
class Level:
    index: int
    name: str
    islands: list
    edges: list
    budget: int
    optimal_cost: int


def _random_spot(index, width, height, rng):
    return Island(index, rng.uniform(MARGIN, width - MARGIN), rng.uniform(MARGIN, height - MARGIN))


def _place_islands(n, width, height, rng):
    islands = []
    attempts = 0
    while len(islands) < n and attempts < 8000:
        attempts += 1
        spot = _random_spot(len(islands), width, height, rng)
        if all(distance(spot, other) >= MIN_GAP for other in islands):
            islands.append(spot)
    while len(islands) < n:
        islands.append(_random_spot(len(islands), width, height, rng))
    return islands


def _crosses_island(islands, a, b):
    p, q = islands[a], islands[b]
    for r in islands:
        if r.id in (a, b):
            continue
        if segment_distance(r.x, r.y, p.x, p.y, q.x, q.y) < CLEARANCE:
            return True
    return False


def generate_level(index, width, height, rng=None):
    rng = rng or random.Random()
    cfg = LEVELS[index]
    n = cfg["islands"]
    islands = _place_islands(n, width, height, rng)

    pairs = sorted(
        (
            (a, b, max(1, round(distance(islands[a], islands[b]) / COST_SCALE)))
            for a in range(n)
            for b in range(a + 1, n)
        ),
        key=lambda t: t[2],
    )
    clear = [t for t in pairs if not _crosses_island(islands, t[0], t[1])]

    chosen = {}
    for i in range(n):
        nearest = [t for t in clear if i in (t[0], t[1])][: cfg["k"]]
        for a, b, w in nearest:
            chosen[(a, b)] = w

    uf = UnionFind(n)
    for a, b in chosen:
        uf.union(a, b)
    for a, b, w in clear + pairs:
        if uf.union(a, b):
            chosen[(a, b)] = w

    edges = [Bridge(a, b, w) for (a, b), w in chosen.items()]
    optimal = sum(e.weight for e in kruskal_mst(edges, n))
    budget = math.ceil(optimal * BUDGET_SLACK / 10) * 10
    return Level(index, cfg["name"], islands, edges, budget, optimal)
