# Isle Weaver

Game puzzle untuk Quiz 2 EF234405 Perancangan dan Analisis Algoritma.

Ada beberapa pulau di peta dan sejumlah calon jembatan dengan biayanya masing-masing.
Tugas pemain: sambungkan semua pulau tanpa melebihi anggaran, dan usahakan semurah mungkin.
Setelah pemain menekan **Submit**, game menjalankan **algoritma Kruskal** untuk mencari
jaringan termurah (Minimum Spanning Tree), lalu membandingkannya dengan hasil pemain.

## Cara menjalankan

```
pip install -r requirements.txt
python main.py
```

Unit test (tidak butuh pygame):

```
python tests/test_algorithms.py
```

## Kontrol

| Aksi | Input |
|---|---|
| Bangun / bongkar jembatan | Klik garis putus-putus |
| Submit | Tombol **Submit** (aktif kalau semua pulau sudah terhubung) |
| Ulangi level | Tombol **Ulangi** atau `R` |
| Level berikutnya | `Spasi` di layar hasil |
| Keluar | `Esc` |

## Level

| Level | Nama | Pulau |
|---|---|---|
| 1 | Gugus Pemula | 6 |
| 2 | Selat Kembar | 8 |
| 3 | Teluk Sunyi | 10 |

Skor: `efisiensi = biaya optimal / biaya pemain x 100%`.
3 bintang kalau efisiensi >= 95%, 2 bintang kalau >= 80%, selain itu 1 bintang.

## Struktur

```
main.py                 loop game dan state
core/graph.py           Island dan Bridge
core/union_find.py      Disjoint Set Union (path compression + union by rank)
core/algorithms.py      kruskal_mst, bfs_connected
core/geometry.py        jarak titik ke garis (untuk klik jembatan)
game/level_generator.py pembuatan peta acak
game/scoring.py         efisiensi dan bintang
ui/renderer.py          semua fungsi gambar
tests/                  unit test
```

## Algoritma

- **Kruskal + Union-Find**: semua calon jembatan diurutkan dari yang termurah, lalu diambil satu per satu
  selama tidak membentuk siklus (dicek dengan Union-Find). Kompleksitas O(E log E).
- **BFS**: dipakai untuk mengecek apakah jembatan yang dipilih pemain sudah menghubungkan semua pulau.
  Kompleksitas O(V + E).
- Generator level memakai k-nearest-neighbour untuk calon jembatan, lalu menambah jembatan termurah
  yang menyambung komponen terpisah (pakai Union-Find) supaya setiap level pasti bisa diselesaikan.
