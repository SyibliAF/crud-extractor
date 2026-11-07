# Kartu Desain
Kartu Desain di bawah berasal dari bagian Syibli Achmad Fazani (lexer dan parser) dan Hadi Fachriansyah (resolver dan analyzer) yang dikerjakan secara berkelompok. 


| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Presedensi dinyatakan dengan satu fungsi per tingkat: `_logical` (OR), `_and`, `_not`, `_comparison`, `_additive`, `_multiplicative`, `_unary`. | Satu fungsi dengan tabel presedensi (precedence climbing). | Grammar di spesifikasi sudah bertingkat, sehingga tiap fungsi bisa dicocokkan dengan satu aturan. Kesalahan seperti Bug 5 langsung terlihat saat membandingkan fungsi dan grammar. |
| 2 | Error recovery berhenti setelah `;`. | Berhenti di keyword awal statement berikutnya (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). | `SELECT` juga muncul di tengah statement (`INSERT ... SELECT`, `IN (SELECT ...)`), sehingga pemotongan di sana menghasilkan error ganda untuk satu statement rusak. Spesifikasi 6 meminta tepat satu error per statement. |
| 3 | `INSERT ... SELECT` memakai ulang `_select()` dan disimpan di field `query` node `Insert`. | Membuat node AST baru untuk `INSERT ... SELECT`. | Spesifikasi 7 melarang perubahan API publik, termasuk field node AST, dan `Insert` sudah punya field `query`. |
| 4 | Komentar blok dibuang di lexer dan tidak menjadi token. | Membuat token `COMMENT` yang dibuang di parser. | Spesifikasi 2.3 menyatakan komentar tidak menghasilkan token. Token komentar hanya menambah pekerjaan di parser tanpa manfaat. |
| 5 | Keyword dikenali dengan menormalisasi lexeme ke huruf besar sebelum dicari di `KEYWORDS`. | Mengisi `KEYWORDS` dengan semua variasi huruf besar/kecil. | Jumlah variasi tidak terbatas (`Select`, `sELect`, dan seterusnya), dan `KEYWORDS` adalah API publik yang isinya tidak boleh diubah. |
| 6 | Scope dibuat sebagai tumpukan: tiap `Scope` menyimpan `parent`, `_push()` membuat scope baru dan `_pop()` menutupnya. Pencarian qualifier berjalan dari scope terdalam ke luar dan berhenti di kecocokan pertama. | Satu dictionary datar berisi semua alias dalam satu statement. | Spesifikasi 4.1 dan 4.3 meminta scope bersarang. Dictionary datar tidak bisa membedakan `p` di subquery dari `p` di query luar, sehingga shadowing dan correlated subquery tidak bisa dinyatakan. Bug 8 dan Bug 9 juga langsung terlihat sebagai pelanggaran urutan atau keseimbangan `_push` dan `_pop`. |
| 7 | Resolver dijalankan sebagai pass terpisah setelah parsing dan mengisi `ColumnRef.resolved` pada AST yang sudah jadi. | Meresolusi alias langsung di parser saat membuat node. | Spesifikasi 7 melarang resolusi di parser. Selain itu, parser tetap bisa dicocokkan fungsi demi fungsi dengan grammar, dan resolver bisa melihat seluruh `FROM` dan `JOIN` sebelum menyentuh kolom di `SELECT`, yang tidak mungkin dilakukan dalam sekali jalan karena daftar kolom ditulis sebelum `FROM`. |
| 8 | Kolom tanpa qualifier hanya dicari di scope terdalam: satu tabel di-resolve ke tabel itu, lebih dari satu diberi warning `ambigu tanpa skema` dengan `resolved` tetap `None`, nol tabel diberi warning. | Menebak tabel pertama saat ambigu, atau mencari sampai ke scope luar. | Tidak ada skema database (spesifikasi 7), jadi tidak ada cara mengetahui tabel mana yang memiliki kolom itu. Menebak menghasilkan `column_usage` yang salah tanpa peringatan, sedangkan warning membuat ketidakpastian terlihat. Spesifikasi 4.3 juga menyatakan hanya scope terdalam yang dilihat. |
| 9 | Subquery di `FROM` di-resolve sebelum scope `SELECT` yang memuatnya dibuat. | Mendeklarasikan semua sumber lebih dulu, lalu meresolusi subquery di dalam scope yang sama. | Spesifikasi 4.4: subquery di `FROM` tidak boleh melihat tabel lain di `FROM` yang sama, tetapi tetap melihat scope di luar. Dengan urutan ini, alias saudara otomatis tidak terlihat tanpa pengecekan tambahan. Dibuktikan oleh `test_tepi_subquery_di_from_tidak_melihat_tabel_saudaranya`. |
| 10 | Analyzer menelusuri AST dengan `_collect` dan `_collect_select`: tabel target diberi hurufnya sendiri (C, U, atau D), dan semua tabel yang ditemukan di dalam subquery diberi `R`. Hasilnya disimpan sebagai himpunan lalu diurutkan C, R, U, D oleh `format_ops`. | Mengekstrak tabel dari teks SQL dengan regex (seperti `baseline/regex_extractor.py`), atau memakai satu huruf yang sama untuk seluruh isi statement. | Spesifikasi 7 melarang analyzer membaca teks mentah atau memakai regex. Hasil `evaluate.py` menunjukkan alasan praktisnya: regex hanya mencapai precision 0,65 karena tertipu komentar, string, dan statement rusak, sedangkan penelusuran AST 1,00. Memakai satu huruf untuk seluruh statement adalah penyebab Bug 7. |











