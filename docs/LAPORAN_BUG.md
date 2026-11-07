# Laporan Bug

Dikerjakan berkelompok. Dokumen ini memuat bagian Syibi Achmad Fazani: lexer dan parser. Bug
pada resolver dan analyzer dilaporkan oleh anggota kedua pada bagian terakhir dokumen ini.

Bug ditemukan dengan membaca kode per tahap dan membandingkannya dengan SPESIFIKASI.md bersama
asisten AI (Claude). Setiap perbaikan diterapkan sendiri dan diverifikasi dengan
`python -m pytest`, `python -m crud.cli` pada file contoh, dan test regresi di
`tests/test_tambahan.py`.

Ringkasan bagian lexer dan parser: 6 bug dan 2 TODO. Test terlihat hanya menangkap sebagian dari
bug ini.

| No | Tahap | Bug | Test regresi |
| --- | --- | --- | --- |
| 1 | Lexer | keyword huruf kecil dianggap identifier | `test_regresi_keyword_campuran_huruf_dinormalisasi` |
| 2 | Lexer | `<>` terpecah menjadi dua token | `test_regresi_operator_tidak_sama_dengan_satu_token` |
| 3 | Lexer | `''` di dalam string memotong string | `test_regresi_kutip_ganda_dalam_string_jadi_satu_token` |
| 4 | Parser | error recovery membuang semua token sampai akhir file | `test_regresi_recovery_berhenti_di_titik_koma` |
| 5 | Parser | `AND` dan `OR` berpresedensi sama | `test_regresi_and_lebih_kuat_dari_or` |
| 6 | Parser | `LEFT OUTER JOIN` ditolak | `test_regresi_left_outer_join` |

---

## Bug 1: Keywrd huruf kecil dianggap identifier

**Ditemukan oleh:** Claude, diverifiksi Syibi. **Diperbaiki oleh:** Syibi.

**Gejala.** `select a from t` menghasilkan empat token `IDENT`. Menurut SPESIFIKASI.md bagian 2.2
keyword tidak peka huruf besar/kecil dan nilainya dinormalisasi ke huruf besar. Akibatnya
`pemeliharaan.sql`, yang ditulis dengan huruf kecil, tidak bisa di-parse.

**Reproduksi minimal.**

```sql
select a from t;
```

**Akar masalah.** Lexer mengenali kata dengan membaca seluruh lexeme lalu mencarinya di tabel
keyword (Bab 4, bagian identifiers and keywords). Tabel `KEYWORDS` hanya berisi huruf besar, tetapi
lexeme dibandingkan apa adanya, jadi `select` tidak ditemukan dan jatuh ke jenis `IDENT`. Di Lox
pencarian memang peka huruf, sedangkan spesifikasi SQL ini meminta sebaliknya, sehingga lexeme
harus dinormalisasi dulu sebelum dicari.

**Perbaikan.** `crud/lexer.py`, fungsi `_word`: pencarian memakai `text.upper()` dan token dibuat
dengan nilai `text.upper()`. Alternatif yang dipertimbangkan: mengisi `KEYWORDS` dengan semua
variasi huruf. Ditolak karena jumlah variasi tidak terbatas dan `KEYWORDS` adalah API publik.

**Test regresi.** `test_regresi_keyword_campuran_huruf_dinormalisasi`.

**Peran AI.** Claude menunjukkan perbedaan antara `_word` dan spesifikasi 2.2. Saya memverifikasi
dengan `tokenize("select a from t")` sebelum dan sesudah perbaikan, dan dengan test lexer.

---

## Bug 2: Opertor `<>` terpecah

**Ditemukan oleh:** Syibli, diverifikasi claude. **Diperbaiki oleh:** Syibi.

**Gejala.** `a <> 1` menghasilkan `OP('<')`, `OP('>')`. Spesifikasi 2.5 meminta satu token `<>`.
Pada `laporan_penjualan.sql` kondisi `o.catatan <> 'FROM rahasia'` gagal di-parse.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE a <> 1;
```

**Akar masalah.** Lexer harus mengambil lexeme terpanjang yang cocok (maximal munch, Bab 4, bagian
longer lexemes). Cabang untuk `<` hanya mengintip satu kemungkinan lanjutan, yaitu `=`. Kemungkinan
`>` tidak diperiksa, sehingga `<` dikeluarkan sebagai token sendiri dan `>` dibaca terpisah.

**Perbaikan.** `crud/lexer.py`, `_scan_token`: setelah `<` dicek `=` lalu `>` lewat `_match`.
Alternatif: memeriksa pasangan operator dari daftar dua karakter. Ditolak karena cabang yang ada
sudah memakai pola `_match`, dan perubahan ini lebih kecil.

**Test regresi.** `test_regresi_operator_tidak_sama_dengan_satu_token`.

**Peran AI.** Claude menunjukkan cabang `<` yang kurang. Verifikasi: hasil `tokenize("a <> 1")` dan
`python -m crud.cli data/sample/laporan_penjualan.sql` tanpa error parse.

---

## Bug 3: Kutip ganda di dalam string memotong string

**Ditemukan oleh:** Claude, diverifikasi Syibli. **Diperbaiki oleh:** Syibi.

**Gejala.** `'O''Brien'` menghasilkan dua token `STRING` (`O` dan `Brien`), bukan satu token bernilai
`O'Brien` (spesifikasi 2.4). `pemeliharaan.sql` memakai `'O''Brien'` dan `'O''Neil'`.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE nama = 'O''Brien';
```

**Akar masalah.** Fungsi `_string` mengakhiri string pada kutip tunggal pertama yang ditemukan.
Untuk membedakan kutip penutup dari kutip yang di-escape, lexer harus melihat satu karakter ke depan
(lookahead, `_peek`, Bab 4, bagian string literals). Tanpa lookahead, `''` dibaca sebagai penutup
lalu pembuka string baru.

**Perbaikan.** `crud/lexer.py`, `_string`: bila setelah kutip masih ada kutip, keduanya dimakan dan
satu kutip ditambahkan ke nilai string. Alternatif: memakai regex untuk seluruh string. Ditolak
karena seluruh lexer ditulis dengan pemindaian manual dan pelacakan baris/kolom ada di `_advance`.

**Test regresi.** `test_regresi_kutip_ganda_dalam_string_jadi_satu_token`.

**Peran AI.** Claude menunjukkan celahnya. Verifikasi: `tokenize("'O''Brien'")` menghasilkan satu
`STRING` bernilai `O'Brien`.

---

## Bug 4: Error recovery membuang seluruh sisa file

**Ditemukan oleh:** Claude, diverifikasi Syibi. **Diperbaiki oleh:** Syibli.

**Gejala.** Pada `campuran_error.sql`, statement valid sesudah statement rusak tidak diproses.
Spesifikasi bagian 6 meminta token dibuang sampai dan termasuk `;` berikutnya, lalu parsing
dilanjutkan.

**Reproduksi minimal.**

```sql
SELECT id nama, FROM x;
DELETE FROM y WHERE id = 1;
```

Sebelum perbaikan: 1 error dan 0 statement. Sesudah: 1 error dan 1 statement (`DELETE`).

**Akar masalah.** Ini panic mode error recovery (Bab 6, bagian syntax errors). Setelah error parser
harus mencapai titik sinkronisasi yang aman. `_synchronize` mengulang `_advance()` sampai `EOF`
tanpa pernah memeriksa titik sinkronisasi. Titik yang dipilih spesifikasi adalah `;`, batas antar
statement.

**Perbaikan.** `crud/parser.py`, `_synchronize`: berhenti setelah mengonsumsi token `SEMICOLON`.
Alternatif: berhenti di keyword awal statement berikutnya. Ditolak, lihat Kartu Desain no. 2.

**Test regresi.** `test_regresi_recovery_berhenti_di_titik_koma`.

**Peran AI.** Claude menunjukkan loop yang tidak berhenti. Verifikasi: jumlah error dan statement
pada reproduksi di atas, dan `python -m crud.cli data/sample/campuran_error.sql --detail d.csv`
memuat `produk` (U) dan `keranjang` (D).

---

## Bug 5: `AND` dan `OR` berpresedensi sama

**Ditemukan oleh:** Claude, diverifikasi Syibi. **Diperbaiki oleh:** Syibi.

**Gejala.** `a = 1 OR b = 2 AND c = 3` diparse sebagai `(a = 1 OR b = 2) AND c = 3`. Spesifikasi 3.1
menyatakan `AND` lebih kuat dari `OR`, sehingga hasil yang benar adalah `a = 1 OR (b = 2 AND c = 3)`.
Bug ini tidak mengubah CRUD matrix, tetapi melanggar spesifikasi.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Dalam recursive descent, satu tingkat presedensi diwakili satu fungsi (Bab 6,
bagian precedence dan associativity). Grammar punya dua aturan, `or_expr` dan `and_expr`, tetapi
kode hanya memiliki satu fungsi `_logical` yang memproses keduanya dalam satu loop. Dengan begitu
operator dibaca dari kiri ke kanan tanpa perbedaan kekuatan.

**Perbaikan.** `crud/parser.py`: `_logical` hanya menangani `OR` dan memanggil fungsi baru `_and`,
yang menangani `AND` dan memanggil `_not`. Alternatif: tabel presedensi dengan precedence climbing.
Ditolak, lihat Kartu Desain no. 1.

**Test regresi.** `test_regresi_and_lebih_kuat_dari_or`.

**Peran AI.** Claude menunjukkan penggabungan dua aturan. Verifikasi: `python -m crud.cli
data/sample/audit.sql --ast` (statement baris 2) menunjukkan `OR` di akar pohon.

---

## Bug 6: `LEFT OUTER JOIN` ditolak

**Ditemukan oleh:** Claude, diverifikasi Syibi. **Diperbaiki oleh:** Syibi.

**Gejala.** Parse error `diharapkan JOIN, ditemukan 'OUTER'`. Grammar: `"LEFT" [ "OUTER" ] "JOIN"`.
`pemeliharaan.sql` memakai bentuk ini.

**Reproduksi minimal.**

```sql
SELECT * FROM a LEFT OUTER JOIN b ON a.x = b.x;
```

**Akar masalah.** Fungsi parser harus menerima semua yang diterima grammar (Bab 6, kesesuaian
fungsi dengan aturan). Tanda kurung siku `[ ... ]` berarti bagian opsional, yang dalam recursive
descent ditulis sebagai pemeriksaan "bila token ini ada, konsumsi". `_join` tidak memuat
pemeriksaan itu untuk `OUTER`.

**Perbaikan.** `crud/parser.py`, `_join`: setelah `LEFT` dipanggil `self._match_kw("OUTER")`.

**Test regresi.** `test_regresi_left_outer_join`.

**Peran AI.** Claude menunjukkan simbol opsional yang hilang. Verifikasi: reproduksi di atas tanpa
parse error dan `pemeliharaan.sql` terproses.

---


## Bug pada resolver dan analyzer (ditulis anggota kedua: [nama anggota 2])

Bagian ini diisi oleh anggota kedua dengan format entri yang sama seperti di atas.