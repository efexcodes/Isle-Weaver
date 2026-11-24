# Isle Weaver

Game puzzle untuk Quiz 2 EF234405 Perancangan dan Analisis Algoritma.

Ada beberapa pulau di peta dan sejumlah calon jembatan dengan biayanya masing-masing.
Tugas pemain: sambungkan semua pulau tanpa melebihi anggaran, dan usahakan semurah mungkin.
Setelah pemain menekan **Selesai**, game menjalankan **algoritma Kruskal** langkah demi langkah
untuk mencari jaringan termurah (Minimum Spanning Tree), lalu membandingkannya dengan hasil pemain.

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
| Pilih level | Klik kartu level di menu, atau tombol `1`-`6` |
| Bangun / bongkar jembatan | Klik garis putus-putus / klik jembatan |
| Minta saran | Tombol **Saran** atau `H` (3x per level) |
| Selesai | Tombol **Selesai** atau `Enter` |
| Lewati animasi Kruskal | `Spasi` atau klik |
| Lihat peta perbandingan | `V` di kartu hasil |
| Ulangi level | Tombol **Ulangi** atau `R` |
| Kembali ke menu | `Esc` |

## Level

| Level | Nama | Pulau | Catatan |
|---|---|---|---|
| 1 | Gugus Pemula | 6 | |
| 2 | Selat Kembar | 8 | |
| 3 | Teluk Sunyi | 10 | |
| 4 | Musim Badai | 12 | badai |
| 5 | Mata Angin | 14 | badai, calon jembatan lebih rapat |
| 6 | Pacu Waktu | 16 | badai + batas waktu 90 detik |

Level berikutnya terbuka setelah level sebelumnya selesai. Bintang terbaik tiap level disimpan di `save.json`.

## Perubahan dari v1.1

- Level 6 dengan batas waktu.
- Animasi Kruskal sekarang menampilkan **setiap langkah**: jembatan yang sedang diperiksa (kuning),
  diambil (hijau), atau dilewati karena membentuk siklus (merah). Bisa dilewati dengan Spasi.
- Peta perbandingan di layar hasil: jembatan pemain yang tidak termasuk MST diberi cahaya merah,
  plus jumlah jembatan yang sama dengan MST.
- Tombol **Saran**: menyorot jembatan termurah yang menyambung dua kelompok pulau berbeda
  (langkah Kruskal berikutnya dari kondisi pemain saat itu).
- Menu pilih level, level terkunci, dan penyimpanan progres.

## Struktur

```
main.py                 loop game dan state
core/graph.py           Island dan Bridge
core/union_find.py      Disjoint Set Union (path compression + union by rank)
core/algorithms.py      kruskal_steps, kruskal_mst, prim_mst, connected_groups, bfs_connected, suggest_bridge
core/geometry.py        jarak titik ke garis
game/level_generator.py pembuatan peta acak
game/scoring.py         efisiensi dan bintang
game/progress.py        simpan/muat bintang
ui/                     warna, layout, renderer
tests/                  unit test
tools/benchmark.py      perbandingan waktu Kruskal vs Prim
```
