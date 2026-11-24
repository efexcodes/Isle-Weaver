import os
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.algorithms import bfs_connected, connected_groups, kruskal_mst, kruskal_steps, prim_mst, suggest_bridge
from core.graph import Bridge
from core.union_find import UnionFind
from game.level_generator import LEVELS, generate_level
from game.progress import is_unlocked, load_progress, save_progress
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


def random_graph(rng, n, density=0.5):
    edges = []
    seen = set()
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < density:
                edges.append(Bridge(i, j, rng.randint(1, 50)))
                seen.add((i, j))
    for i in range(n - 1):
        if (i, i + 1) not in seen:
            edges.append(Bridge(i, i + 1, rng.randint(1, 50)))
    return edges


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


def test_kruskal_steps():
    print("Langkah Kruskal")
    edges = [Bridge(0, 1, 1), Bridge(1, 2, 2), Bridge(0, 2, 3), Bridge(2, 3, 4)]
    steps = kruskal_steps(edges, 4)
    check("sisi diperiksa urut dari yang termurah", [e.weight for e, _ in steps] == [1, 2, 3, 4])
    check("sisi 0-2 ditolak karena membentuk siklus", [ok for _, ok in steps] == [True, True, False, True])
    check("berhenti setelah n-1 sisi diambil", sum(ok for _, ok in steps) == 3)


def test_kruskal_vs_prim():
    print("Kruskal vs Prim-Jarnik (20 graf acak)")
    rng = random.Random(42)
    for trial in range(20):
        n = rng.randint(4, 14)
        edges = random_graph(rng, n)
        k = sum(e.weight for e in kruskal_mst(edges, n))
        p = sum(e.weight for e in prim_mst(edges, n))
        check(f"graf {trial + 1}: kruskal={k} prim={p}", k == p)


def test_bfs():
    print("BFS keterhubungan")
    chain = [Bridge(0, 1, 1), Bridge(1, 2, 1)]
    check("rantai 0-1-2 terhubung (3 pulau)", bfs_connected(chain, 3))
    check("rantai 0-1-2 tidak terhubung jika ada pulau ke-4", not bfs_connected(chain, 4))
    check("satu pulau tanpa jembatan dianggap terhubung", bfs_connected([], 1))
    check("dua pulau tanpa jembatan tidak terhubung", not bfs_connected([], 2))
    check("jumlah kelompok dihitung benar", connected_groups([Bridge(0, 1, 1), Bridge(2, 3, 1)], 5) == 3)


def test_suggest_bridge():
    print("Saran jembatan")
    edges = [Bridge(0, 1, 5), Bridge(1, 2, 3), Bridge(0, 2, 1), Bridge(2, 3, 9)]
    edges[2].selected = True
    pick = suggest_bridge(edges, 4)
    check("memilih sisi termurah yang menyambung dua kelompok", pick is edges[1])
    edges[1].selected = True
    check("tidak menyarankan sisi yang membuat siklus", suggest_bridge(edges, 4) is edges[3])
    edges[3].selected = True
    check("tidak ada saran jika sudah terhubung", suggest_bridge(edges, 4) is None)


def test_scoring():
    print("Skor")
    check("biaya sama dengan optimal = 100%", efficiency_percent(120, 120) == 100)
    check("biaya 0 = 0%", efficiency_percent(0, 50) == 0)
    check("95% dapat 3 bintang", stars_for_efficiency(95) == 3)
    check("80% dapat 2 bintang", stars_for_efficiency(80) == 2)
    check("di bawah 80% dapat 1 bintang", stars_for_efficiency(79) == 1)


def test_progress():
    print("Simpan progres")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "save.json"
        check("file belum ada -> progres kosong", load_progress(path) == {})
        save_progress({0: 3, 1: 2}, path)
        check("progres tersimpan dan terbaca lagi", load_progress(path) == {0: 3, 1: 2})
        path.write_text("bukan json", encoding="utf-8")
        check("file rusak tidak membuat game crash", load_progress(path) == {})
    check("level 1 selalu terbuka", is_unlocked({}, 0))
    check("level 2 terkunci sebelum level 1 selesai", not is_unlocked({}, 1))
    check("level 2 terbuka setelah level 1 selesai", is_unlocked({0: 1}, 1))


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
            ok_budget &= level.optimal_cost == sum(e.weight for e in prim_mst(level.edges, n))
        check(f"level {i + 1}: jumlah pulau = {cfg['islands']}", ok_count)
        check(f"level {i + 1}: graf kandidat selalu terhubung", ok_conn)
        check(f"level {i + 1}: anggaran cukup tapi tidak berlebihan", ok_budget)


if __name__ == "__main__":
    test_union_find()
    test_kruskal_known_graph()
    test_kruskal_steps()
    test_kruskal_vs_prim()
    test_bfs()
    test_suggest_bridge()
    test_scoring()
    test_progress()
    test_levels()
    print(f"\n{passed} lulus, {failed} gagal")
    sys.exit(1 if failed else 0)
