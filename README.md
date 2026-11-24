# Isle Weaver

Game puzzle untuk Quiz 2 EF234405 Perancangan dan Analisis Algoritma.

Ada beberapa pulau di peta dan sejumlah calon jembatan dengan biayanya masing-masing.
Tugas pemain: sambungkan semua pulau tanpa melebihi anggaran, dan usahakan semurah mungkin.
Setelah pemain menekan **Selesai**, game menjalankan **algoritma Kruskal** untuk mencari
jaringan termurah (Minimum Spanning Tree), lalu membandingkannya dengan hasil pemain.

## Cara menjalankan

```
pip install -r requirements.txt
python main.py
```

Unit test dan benchmark (tidak butuh pygame):

```
python tests/test_algorithms.py
python tools/benchmark.py
```

## Kontrol

| Aksi | Input |
|---|---|
| Bangun / bongkar jembatan | Klik garis putus-putus / klik jembatan |
| Selesai | Tombol **Selesai** atau `Enter` |
| Ulangi level | Tombol **Ulangi** atau `R` |
| Level berikutnya | `Spasi` atau tombol **Lanjut** di kartu hasil |
| Kembali ke menu | `Esc` |

## Level

| Level | Nama | Pulau | Catatan |
|---|---|---|---|
| 1 | Gugus Pemula | 6 | |
| 2 | Selat Kembar | 8 | |
| 3 | Teluk Sunyi | 10 | |
| 4 | Musim Badai | 12 | badai |
| 5 | Mata Angin | 14 | badai, calon jembatan lebih rapat |

Saat badai, setiap 4 detik sekitar 30% jembatan yang belum dibangun harganya naik 60%.
Jembatan yang sudah dibangun harganya dikunci, jadi badai berikutnya tidak mengubah biaya yang sudah dibayar.

## Perubahan dari v1.0

- Tampilan baru: pulau berbentuk organik, jembatan kayu, ombak bergerak, kompas, label biaya berbentuk pil.
- Layar judul.
- Level 4 dan 5 dengan mekanik badai.
- Highlight jembatan saat kursor diarahkan, angka biaya melayang saat membangun/membongkar.
- Status menunjukkan berapa kelompok pulau yang masih terpisah (BFS menghitung komponen).
- Implementasi **Prim-Jarnik** untuk pembanding, plus `tools/benchmark.py` untuk mengukur waktu Kruskal vs Prim.

## Struktur

```
main.py                 loop game dan state
core/graph.py           Island dan Bridge
core/union_find.py      Disjoint Set Union (path compression + union by rank)
core/algorithms.py      kruskal_mst, prim_mst, connected_groups, bfs_connected
core/geometry.py        jarak titik ke garis
game/level_generator.py pembuatan peta acak
game/scoring.py         efisiensi dan bintang
ui/                     warna, layout, renderer
tests/                  unit test
tools/benchmark.py      perbandingan waktu Kruskal vs Prim
```
