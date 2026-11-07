# Kartu Desain

Lima keputusan di bawah berasal dari bagian Syibli Achmad Fazani (lexer dan parser) yang dikerjakan secara berkelompok. Keputusan desain pada resolver dan analyzer dapat ditambahkan anggota kedua pada bagian terakhir dokumen ini.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Presedensi dinyatakan dengan satu fungsi per tingkat: `_logical` (OR), `_and`, `_not`, `_comparison`, `_additive`, `_multiplicative`, `_unary`. | Satu fungsi dengan tabel presedensi (precedence climbing). | Grammar di spesifikasi sudah bertingkat, sehingga tiap fungsi bisa dicocokkan dengan satu aturan. Kesalahan seperti Bug 5 langsung terlihat saat membandingkan fungsi dan grammar. |
| 2 | Error recovery berhenti setelah `;`. | Berhenti di keyword awal statement berikutnya (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). | `SELECT` juga muncul di tengah statement (`INSERT ... SELECT`, `IN (SELECT ...)`), sehingga pemotongan di sana menghasilkan error ganda untuk satu statement rusak. Spesifikasi 6 meminta tepat satu error per statement. |
| 3 | `INSERT ... SELECT` memakai ulang `_select()` dan disimpan di field `query` node `Insert`. | Membuat node AST baru untuk `INSERT ... SELECT`. | Spesifikasi 7 melarang perubahan API publik, termasuk field node AST, dan `Insert` sudah punya field `query`. |
| 4 | Komentar blok dibuang di lexer dan tidak menjadi token. | Membuat token `COMMENT` yang dibuang di parser. | Spesifikasi 2.3 menyatakan komentar tidak menghasilkan token. Token komentar hanya menambah pekerjaan di parser tanpa manfaat. |
| 5 | Keyword dikenali dengan menormalisasi lexeme ke huruf besar sebelum dicari di `KEYWORDS`. | Mengisi `KEYWORDS` dengan semua variasi huruf besar/kecil. | Jumlah variasi tidak terbatas (`Select`, `sELect`, dan seterusnya), dan `KEYWORDS` adalah API publik yang isinya tidak boleh diubah. |
