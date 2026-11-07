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


## Bug pada resolver dan analyzer (Hadi Fachriansyah)


Ringkasan bagian resolver dan analyzer: 3 bug dan 1 TODO (T2). Satu bug ditangkap test terlihat; dua bug resolver tidak mengubah CRUD matrix sehingga tidak tertangkap test terlihat.


| No | Tahap | Bug | Test regresi |
| --- | --- | --- | --- |
| 7 | Analyzer | tabel di subquery pada `UPDATE` ditandai `U`, bukan `R` | `test_regresi_update_subquery_di_where_dan_set_hanya_membaca` |
| 8 | Resolver | `_lookup` mencari scope dari luar ke dalam | `test_regresi_alias_subquery_menutupi_alias_luar` |
| 9 | Resolver | `_delete` tidak menutup scope-nya | `test_regresi_alias_delete_tidak_bocor_ke_statement_berikutnya` |
| T2 | Resolver | kolom tanpa qualifier tidak di-resolve (TODO) | `test_kolom_tanpa_qualifier_dua_tabel`, `test_kolom_tanpa_qualifier_tanpa_tabel` |


---


## Bug 7: Tabel di subquery pada UPDATE ditandai U


**Ditemukan oleh:** test terlihat `test_matrix_laporan_penjualan` yang gagal; Claude menunjuk cabang `UPDATE`. **Diperbaiki oleh:** Hadi.


**Gejala.** Pada `laporan_penjualan.sql` tabel `pesanan` bergabung menjadi `RUD`, seharusnya `RD`. `--detail` menampilkan baris `UPDATE,pesanan,U` padahal `pesanan` hanya dibaca di subquery. Spesifikasi bagian 5: membaca tabel lewat subquery selalu `R`, apa pun jenis statement luarnya.


**Reproduksi minimal.**


```sql
UPDATE pelanggan SET level = 'gold'
WHERE id IN (SELECT pelanggan_id FROM pesanan);
```


Sebelum perbaikan: `pelanggan` U dan `pesanan` U. Sesudah: `pelanggan` U dan `pesanan` R.


**Akar masalah.** Analyzer menelusuri pohon AST dan membawa satu parameter `op` ke semua node anak (penelusuran pohon, Bab 5). Cabang `UPDATE` memanggil `_collect(..., "U")` untuk nilai `SET` dan `WHERE`, sehingga huruf yang seharusnya hanya milik tabel target ikut diberikan ke setiap tabel di dalam subquery. Peran sebuah tabel (target yang diubah atau sumber yang dibaca) ditentukan oleh posisinya di pohon, bukan oleh jenis statement luarnya. Cabang `DELETE` sudah benar memakai `"R"`; perbedaan itu menjadi petunjuk.


**Perbaikan.** `crud/analyzer.py`, `analyze_statement`, cabang `UPDATE`: `"U"` diganti `"R"` pada dua pemanggilan `_collect` (nilai `SET` dan `WHERE`). Target tetap ditandai `U` lewat `usage[stmt.table.name].add("U")`. Alternatif: fungsi terpisah `_collect_reads` tanpa parameter `op`, sehingga salah huruf tidak mungkin terjadi. Ditolak karena perubahannya lebih besar dan `_collect` juga dipakai oleh `INSERT`, `DELETE`, dan `SELECT`.


**Test regresi.** `test_regresi_update_subquery_di_where_dan_set_hanya_membaca` (subquery di `WHERE` dan di `SET`).


**Peran AI.** Claude menunjuk cabang `UPDATE` dan menulis test regresi. Perbaikan saya terapkan sendiri. Verifikasi: `test_matrix_laporan_penjualan` lulus, `--detail` tidak lagi memuat `pesanan` dengan `U`, dan test regresi gagal sebelum perbaikan dan lulus sesudahnya.


---


## Bug 8: Pencarian alias dimulai dari scope terluar


**Ditemukan oleh:** Claude, diverifikasi Hadi dengan reproduksi. **Diperbaiki oleh:** Hadi.


**Gejala.** Pada subquery yang memakai alias yang sama dengan query luar, `p.id` di dalam subquery ter-resolve ke tabel milik query luar. Spesifikasi 4.3: qualifier dicari dari scope terdalam ke luar dan yang pertama ditemukan dipakai (shadowing). Bug ini tidak mengubah CRUD matrix, tetapi melanggar spesifikasi. Kasus ini ada di `audit.sql` baris 12 sampai 14.


**Reproduksi minimal.**


```sql
SELECT p.a FROM pelanggan p
WHERE EXISTS (SELECT 1 FROM pesanan p WHERE p.id = 1);
```


Sebelum perbaikan: `p.id` ter-resolve ke `pelanggan`. Sesudah: `pesanan`.


**Akar masalah.** Resolver menyimpan scope sebagai tumpukan dan mencari nama dari scope teratas (terdalam) ke bawah (Bab 11, bagian resolving variables); pencocokan pertama menang. `_lookup` mengumpulkan rantai scope mulai dari scope saat ini lalu mengikuti `parent`, sehingga urutan `chain` sudah dari terdalam ke terluar. Lalu loop pencarian memakai `reversed(chain)`, sehingga urutannya terbalik menjadi terluar dulu dan deklarasi luar menutupi deklarasi dalam, kebalikan dari shadowing.


**Perbaikan.** `crud/resolver.py`, `_lookup`: `for scope in reversed(chain)` diganti `for scope in chain`. Alternatif: menelusuri `scope = scope.parent` langsung di satu loop tanpa membuat daftar. Ditolak karena perubahan satu kata lebih kecil dan menjaga struktur fungsi.


**Test regresi.** `test_regresi_alias_subquery_menutupi_alias_luar`.


**Peran AI.** Claude menunjukkan gejalanya dan menulis test regresi, lalu memeberitahu logika `reversed`. lalu saya menemukan penyebabnya di `reversed(chain)` yang dimana saya ubah jadi chain. Verifikasi: test gagal sebelum perbaikan dan lulus sesudahnya, seluruh `python -m pytest` hijau.


---


## Bug 9: Scope dari DELETE tidak ditutup


**Ditemukan oleh:** Claude, diverifikasi Hadi dengan reproduksi. **Diperbaiki oleh:** Hadi.


**Gejala.** Alias dari statement `DELETE` masih terlihat oleh statement berikutnya, dan setelah script selesai masih ada scope tersisa. Spesifikasi 4.5: setiap statement berdiri sendiri dan tidak boleh ada scope tersisa. Kasus ini ada di `audit.sql` baris 16 dan 18 (`s.id` seharusnya error).


**Reproduksi minimal.**


```sql
DELETE FROM pesanan o WHERE id = 1;
SELECT o.id FROM pelanggan;
```


Sebelum perbaikan: `o.id` ter-resolve ke `pesanan` tanpa diagnostik. Sesudah: error `alias 'o' tidak terdefinisi`.


**Akar masalah.** Setiap `beginScope` harus dipasangkan dengan `endScope` agar tumpukan scope seimbang (Bab 11, bagian scopes). `_update` dan `_select` memanggil `_push()` lalu `_pop()`, tetapi `_delete` hanya memanggil `_push()`. Scope miliknya tertinggal di tumpukan, sehingga statement berikutnya mencari nama di dalamnya, dan tumpukan makin dalam untuk setiap `DELETE`.


**Perbaikan.** `crud/resolver.py`, `_delete`: menambah `self._pop()` setelah `self._expr(dele.where)`. Alternatif: membungkus dengan `try/finally`. Ditolak karena `_select` dan `_update` tidak memakainya dan resolver tidak melempar exception.


**Test regresi.** `test_regresi_alias_delete_tidak_bocor_ke_statement_berikutnya` (memeriksa error, `resolved` bernilai `None`, dan `resolver.scope is None`).


**Peran AI.** Claude menunjukkan gejalanya dan menulis test regresi. namun penyebab (`_pop()` hilang) dan perbaikannya saya cari dan tulis sendiri dengan membandingkan `_delete` dengan `_update`. Verifikasi: test gagal sebelum perbaikan dan lulus sesudahnya.


---


## TODO T2: Kolom tanpa qualifier


**Dikerjakan oleh:** Hadi, dengan bantuan Claude.


**Gejala.** Pada `SELECT nama FROM pelanggan WHERE aktif = 1`, `ColumnRef.resolved` bernilai `None`. Test terlihat `test_kolom_tanpa_qualifier_satu_tabel` gagal.


**Akar masalah.** Bagian ini belum diimplementasikan; cabang untuk kolom tanpa qualifier hanya berisi `pass`. Tabel sudah masuk scope lewat `_declare_source`, tetapi tidak ada kode yang menghubungkan kolom ke tabel itu. Berbeda dengan qualifier, kolom tanpa qualifier hanya melihat scope terdalam (spesifikasi 4.3), karena tanpa skema tidak ada cara menebak tabel di scope luar.


**Implementasi.** `crud/resolver.py`, `_column`: bila tepat satu tabel di scope terdalam, `resolved` diisi tabel itu (lewat `_target_of`). Bila lebih dari satu, warning `kolom 'x' ambigu tanpa skema` dan `resolved` tetap `None`. Bila tidak ada tabel (misalnya kolom di `INSERT ... VALUES`, yang tidak membuat scope), warning. Alternatif: menebak tabel pertama bila ambigu, atau mencari ke scope luar. Ditolak karena tidak ada skema database (spesifikasi 7) dan spesifikasi 4.3 menyatakan hanya scope terdalam.


**Test.** `test_kolom_tanpa_qualifier_satu_tabel` (terlihat), `test_kolom_tanpa_qualifier_dua_tabel`, dan `test_kolom_tanpa_qualifier_tanpa_tabel` (tambahan).


**Peran AI.** saya memikirkan logika nya dan claude membantu menulis blok kode T2 . Verifikasi: ketiga test lulus.

















