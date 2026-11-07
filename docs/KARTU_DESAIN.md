# Laporan Akhir


Dikerjakan berkelompok. Bagian yang ditulis di sini berasal dari pekerjaan Syibi Achmad Fazani
(lexer dan parser) dan Hadi Fachriansyah (analyzer dan resolver)


## 1. Hasil evaluasi


Keluaran `python evaluate.py` pada kode dengan seluruh perbaikan, setelah `data/ground_truth.csv`
dilengkapi untuk keempat file contoh. Label `audit.sql` dan `pemeliharaan.sql` dibuat dengan membaca
SQL dan SPESIFIKASI.md, lalu dibandingkan dengan keluaran tool setelah label selesai.


```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)


Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72


[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```


Pada 27 triple, parser memperoleh precision, recall, dan F1 sebesar 1,00. Baseline regex memperoleh
precision 0,65, recall 0,81, dan F1 0,72. Angka parser sempurna hanya berlaku untuk empat file
contoh ini. Hasil itu bukan bukti bahwa tool benar untuk semua SQL, karena file contoh sengaja
dibuat memuat jebakan yang sudah diperbaiki.


## 2. Tiga kasus di mana regex salah


Regex memotong teks pada `;` lalu mencari pola `FROM`, `JOIN`, `INSERT INTO`, `UPDATE`, dan
`DELETE FROM`. Ia tidak membedakan kode dari komentar atau string, dan tidak memahami struktur
statement.


1. Komentar yang berisi SQL. Baris 2 `laporan_penjualan.sql`:


   ```sql
   -- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
   ```


   Regex melaporkan `pelanggan` dengan operasi D dan R, padahal tidak ada perintah hapus. Komentar
   itu juga membuat regex mengira statement dimulai di baris 2 (statement sebenarnya di baris 3),
   sehingga triple yang benar untuk baris 3 terlewat. Kasus serupa terjadi di `pemeliharaan.sql`:
   `UPDATE pelanggan_lama` di dalam komentar dilaporkan sebagai U. Parser benar karena lexer
   membuang komentar sebelum parser melihat token apa pun (Bab 4). Regex bekerja pada teks mentah
   tanpa tahap lexing.


2. Kata kunci di dalam string. Baris 6 `laporan_penjualan.sql`:


   ```sql
   WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
   ```


   Regex menganggap `FROM rahasia` sebagai klausa dan melaporkan tabel `rahasia` dibaca. Parser
   benar karena lexer mengubah seluruh isi tanda kutip menjadi satu token `STRING`, sehingga kata
   di dalamnya tidak pernah dianggap keyword.


3. Satu statement, dua peran. Baris 16 `audit.sql`:


   ```sql
   DELETE FROM sesi s WHERE s.kedaluwarsa < :sekarang;
   ```


   Pola `DELETE FROM` dan pola `FROM` sama-sama cocok pada teks ini, sehingga `sesi` dilaporkan D dan
   R. Kesalahan yang sama muncul untuk `keranjang`, `pesanan` (baris 15), dan `crm.alamat`. Parser
   benar karena grammar `delete_stmt` menetapkan tepat satu tabel target dengan operasi D (Bab 6:
   statement diparse oleh aturan grammar, bukan pencocokan pola).


Temuan lain dari hasil evaluasi: pada `FROM pelanggan p, pesanan o` regex hanya mengambil nama
sesudah `FROM`, sehingga `pesanan` terlewat (`audit.sql` baris 2). Regex juga menghitung statement
yang salah sintaks (`campuran_error.sql` baris 4), sedangkan spesifikasi 5 menyatakan statement
yang gagal di-parse tidak dihitung.


## 3. Batas pendekatan kami


Bagian lexer dan parser. Hal-hal berikut tidak ditangani meskipun semua bug sudah diperbaiki.


1. Konstruksi di luar lingkup (spesifikasi bagian 9): `WITH` (CTE), `UNION`, `MERGE`, DDL.
   `WITH x AS (SELECT 1 FROM a) SELECT * FROM x;` menghasilkan parse error di `WITH` dan
   `CREATE TABLE z (id INT);` menghasilkan parse error di `CREATE`. Pada
   `SELECT a FROM t UNION SELECT a FROM u;`, kata `UNION` terbaca sebagai alias tabel `t`, sehingga
   error muncul di `SELECT` kedua. Pada semua kasus ini statement tidak dihitung, jadi tabel di
   dalamnya tidak muncul di matrix (false negative). Yang dibutuhkan: grammar yang mencakup
   konstruksi itu dan, untuk CTE, nama tabel sementara.


2. Karakter yang tidak dikenal lexer menghentikan pemrosesan seluruh file (spesifikasi 2.7).
   Contoh: quoted identifier (`"a"`) dan operator `%` menghasilkan `LexError`. Pada file dua
   statement yang statement pertamanya memakai `"a"`, statement kedua (`DELETE FROM u`) yang valid
   ikut tidak dihitung dan matrix file itu kosong. Berbeda dengan error sintaks, `LexError` tidak
   punya mekanisme pemulihan. Yang dibutuhkan: pemulihan di tingkat lexer, atau dukungan untuk
   karakter tersebut.


3. Satu kesalahan sintaks menghilangkan satu statement utuh dari matrix. Pada
   `campuran_error.sql`, statement baris 4 diabaikan seluruhnya, termasuk tabel `pesanan` di
   dalamnya. Pendekatan ini sengaja dipilih spesifikasi, tetapi menimbulkan false negative bila
   ada salah ketik kecil. Pemulihan juga bergantung pada `;`: bila `;` hilang antara dua statement,
   keduanya hilang sampai `;` berikutnya.


4. `t.*` (spesifikasi 9, di luar lingkup) ditolak parser dengan error `diharapkan nama kolom setelah
   '.', ditemukan '*'`. Statement yang memakainya tidak dihitung.


Bagian resolver dan analyzer, hal-hal berikut juga tidak ditangani dengan benar
meskipun semua bug sudah diperbaiki.


1. Tidak ada skema database (spesifikasi 7). Pada `SELECT nama FROM pelanggan, pemesan` kolom `nama`
   bisa milik salah satu tabel. Resolver hanya bisa memberi warning `ambigu tanpa skema` dan
   membiarkan `resolved` bernilai `None`. Akibatnya kolom itu tidak muncul di keluaran `--kolom`
   (CRUD matrix tingkat tabel tidak terpengaruh). Yang dibutuhkan: katalog yang memuat kolom
   setiap tabel.


2. Kolom tanpa qualifier di subquery diselesaikan ke tabel scope terdalam, bahkan bila sebenarnya
   milik query luar. Pada `SELECT 1 FROM pelanggan WHERE EXISTS (SELECT 1 FROM pesanan WHERE level =
   'gold')`, kolom `level` di-resolve ke `pesanan` tanpa warning, padahal bila `level` adalah kolom
   `pelanggan` hasilnya salah. Ini konsekuensi aturan spesifikasi 4.3 (hanya scope terdalam untuk
   kolom tanpa qualifier) dan salah diam-diam, lebih buruk daripada warning. Akibatnya `--kolom`
   mengaitkan kolom ke tabel yang salah. Yang dibutuhkan: skema, untuk memeriksa tabel mana yang
   benar-benar punya kolom itu.


3. View, trigger, dan stored procedure tidak terlihat (spesifikasi 9). `SELECT * FROM v_laporan`
   menghasilkan `v_laporan` R; tabel dasar di balik view tidak muncul, dan efek trigger pada
   `INSERT` ke suatu tabel tidak tercatat. Matrix mencatat akses yang tertulis, bukan akses yang
   terjadi. Yang dibutuhkan: definisi view dan trigger dari database.


4. Error resolver tidak mengubah matrix. Pada `audit.sql` baris 18 alias `s` tidak terdefinisi,
   tetapi `pengguna` tetap dihitung R, karena spesifikasi 5 hanya mengecualikan statement yang
   gagal di-parse. Statement yang tidak valid secara semantik tetap masuk matrix. Pembaca matrix
   harus membaca diagnostik secara terpisah.




## 4. Pembagian kerja


Syibi Achmad Fazani: lexer, parser, dan test regresi serta kasus tepi untuk keduanya.
Hadi Fachriansyah: resolver, analyzer, dan test regresi serta kasus tepi untuk
keduanya.
lalu di akhir waktu, kami menjelaskan satu sama lain apa yang dikerjakan, dan bagaimana kasus tersebut diselesaikan, bila terjadi perbedaan pemahaman, maka masing masing prompting ai dengan pemahaman sendiri sehingga keduanya mengerti



