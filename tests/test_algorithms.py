import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.algorithms import bfs_connected, kruskal_mst
from core.graph import Bridge
from core.union_find import UnionFind
from game.level_generator import LEVELS, generate_level
from game.scoring import efficiency_percent, stars_for_efficiency

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [OK]   {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


def test_union_find():
    print("Union-Find")
    uf = UnionFind(5)
    check("awalnya semua terpisah", not uf.connected(0, 1))
    check("union pertama mengembalikan True", uf.union(0, 1) is True)
    check("setelah union jadi terhubung", uf.connected(0, 1))
    check("union ulang mengembalikan False", uf.union(0, 1) is False)
    uf.union(2, 3)
    check("0-1 dan 2-3 masih terpisah", not uf.connected(0, 2))
    uf.union(1, 2)
    check("dua kelompok tergabung", uf.connected(0, 3))


def test_kruskal_known_graph():
    print("Kruskal pada graf kecil")
    edges = [Bridge(0, 1, 1), Bridge(1, 2, 1), Bridge(2, 3, 1), Bridge(3, 0, 1), Bridge(0, 2, 2)]
    mst = kruskal_mst(edges, 4)
    check("MST punya n-1 sisi", len(mst) == 3)
    check("biaya MST = 3", sum(e.weight for e in mst) == 3)


def test_bfs():
    print("BFS keterhubungan")
    chain = [Bridge(0, 1, 1), Bridge(1, 2, 1)]
    check("rantai 0-1-2 terhubung (3 pulau)", bfs_connected(chain, 3))
    check("rantai 0-1-2 tidak terhubung jika ada pulau ke-4", not bfs_connected(chain, 4))
    check("satu pulau tanpa jembatan dianggap terhubung", bfs_connected([], 1))
    check("dua pulau tanpa jembatan tidak terhubung", not bfs_connected([], 2))


def test_scoring():
    print("Skor")
    check("biaya sama dengan optimal = 100%", efficiency_percent(120, 120) == 100)
    check("biaya 0 = 0%", efficiency_percent(0, 50) == 0)
    check("95% dapat 3 bintang", stars_for_efficiency(95) == 3)
    check("80% dapat 2 bintang", stars_for_efficiency(80) == 2)
    check("di bawah 80% dapat 1 bintang", stars_for_efficiency(79) == 1)


def test_levels():
    print(f"Generator level ({len(LEVELS)} level x 30 seed)")
    for i, cfg in enumerate(LEVELS):
        ok_count = ok_conn = ok_budget = True
        for seed in range(30):
            level = generate_level(i, 920, 474, random.Random(seed))
            n = len(level.islands)
            ok_count &= n == cfg["islands"]
            ok_conn &= bfs_connected(level.edges, n)
            ok_budget &= level.optimal_cost <= level.budget <= level.optimal_cost * 2
        check(f"level {i + 1}: jumlah pulau = {cfg['islands']}", ok_count)
        check(f"level {i + 1}: graf kandidat selalu terhubung", ok_conn)
        check(f"level {i + 1}: anggaran cukup tapi tidak berlebihan", ok_budget)


if __name__ == "__main__":
    test_union_find()
    test_kruskal_known_graph()
    test_bfs()
    test_scoring()
    test_levels()
    print(f"\n{passed} lulus, {failed} gagal")
    sys.exit(1 if failed else 0)
