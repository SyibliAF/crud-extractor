# Log Penggunaan AI


AI yang dipakai: Claude (Anthropic), lewat browser dan Copilot agent VSCode untuk mengecek penulisan seperti indentasi/typo karena bisa mengubah file yang sedang dikerjakan.


## Anggota 1: Syibi Achmad Fazani


AI yang dipakai CLAUDE & COPILOT


| No | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- |
| 1 | Minta dipandu mengerjakan tugas langkah demi langkah karena belum memahami alurnya. | Diterima: gambaran pipeline (lexer, parser, resolver, analyzer) dan urutan kerja. | Perlu peta sebelum membaca kode. | Dicocokkan dengan deskripsi tugas dan SPESIFIKASI.md. |
| 2 | Bantuan alat: terminal dan editor di VS Code, Git, branch, push ke GitHub, pemilihan akun GitHub. | Diterima. | Belum terbiasa dengan alat tersebut. Tidak memengaruhi isi kode. | Perintah dijalankan dan hasilnya dilihat langsung. |
| 3 | Minta Claude membaca kode lexer dan membandingkannya dengan spesifikasi bagian 2. | Diterima: empat perubahan (komentar blok, keyword huruf kecil, `<>`, `''`). Isi lengkap `lexer.py` diberikan Claude dan ditempel ke editor. | Keempatnya sesuai spesifikasi 2.2 sampai 2.5. | `python -m pytest`: test lexer lulus. |
| 4 | Minta langkah demi langkah untuk melakukan test regresi lexer. | Diterima: 1 contoh test di `tests/test_tambahan.py`. Penempelan pertama gagal dengan `IndentationError` karena spasi ikut tertempel. Diperbaiki dengan menempel ulang dari kolom paling kiri. | Tiap test mewakili satu perbaikan lexer. | `python -m pytest tests/test_tambahan.py`: 1 lulus. |




## Anggota 2: Hadi Fachriansyah


Alat: Claude (chat). Claude membaca repo dengan meng-clone-nya ke sandbox miliknya sendiri; kode di repo kami tidak diubah oleh Claude, semua perubahan kami salin dan commit sendiri. 


| No | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- |
| 1 | Asked what the task requires and what each file does (lexer, parser, resolver, analyzer, pipeline, cli). | Diterima: rencana kerja dan penjelasan pipeline. | Belum paham alur dan struktur kode. | mencocokan pemahaman dengan kode yang tersedia |
| 2 | Asked how to run tests and what SPESIFIKASI.md section 7 (public API) allows. | Diterima: pakai `python -m pytest`; nama dan bentuk keluaran API publik tidak boleh berubah. | Aturan bagian 7 kurang jelas. | Memeriksa perbaikan tidak mengubah nama atau signature publik. |
| 3 | `test_matrix_laporan_penjualan` failed (`pesanan` RUD, expected RD). Asked for help tracing it. | claude membantu logika pada test dan code; saya mencoba mengganti `"U"` menjadi `"R"` di CRUD. | Subquery di UPDATE harus R. | Test lulus. |
| 4 | Asked for a regression test for that analyzer bug. | Diterima: 1 test (subquery di SET dan WHERE). | Belum tahu bentuk test regresi. | Dicek gagal sebelum perbaikan dan lulus sesudahnya. |
| 5 | `test_kolom_tanpa_qualifier_satu_tabel` failed. Asked Claude to write TODO(T2) and its tests. | Diterima: blok T2 di `_column` dari Claude.. | Belum paham 4.3. | pytest lulus. |
| 6 | Asked Claude for tests of two resolver bugs (shadowing, scope leak after DELETE). | Diterima: dua test dari Claude. dan saya menganalisa kode dan menemukan penyebabnya (`self._pop()` di `_delete`, `for scope in chain:` di `_lookup`) | Perlu test sebelum memperbaiki. | Kedua test gagal sebelumnya dan lulus sesudah perbaikan. |
| 7 | Asked what FP, FN, precision, recall, and F1 in `evaluate.py` mean and why regex makes errors. | Diterima: penjelasan yang mendalam mengenai istilah tersebut. | Belum paham metrik. | Menghitung ulang dari keluaran evaluate. |
| 8 | checking `ground_truth.csv` labels for `audit.sql` and `pemeliharaan.sql`. | Diubah: 3 kesalahan yang dikoreksi (nomor baris, typo, huruf `I` → `C`). | verifikasi jika ada kesalahan. | `evaluate.py`: parser F1 = 1.00 pada 4 file. |
| 9 | Asked for 5 edge-case tests (analyzer and resolver only). | Diterima: 5 test dari Claude (2 analyzer, 3 resolver). | bingung untuk menulis edge test analyzer dan resolver. | Semua lulus di repo . |










## Refleksi


AI paling membantu dalam membaca kode terhadap spesifikasi secara sistematis: bug yang tidak
tertangkap test terlihat, misalnya `<>`, `''`, dan error recovery, ditemukan dengan cara itu. Claude
juga menjelaskan konsep bab yang terkait dengan tiap bug. Ada beberapa kekeliruan. Di awal Claude
memakai istilah "terminal" tanpa menjelaskan bahwa kode diubah di editor dan bukan di terminal, dan
perintah Git yang ditempel sekaligus tidak berjalan sebagaimana mestinya. Claude juga tidak bisa
menjalankan pytest asli di lingkungannya (pytest tidak dapat dipasang) dan memakai pengganti
sederhana, sehingga hasil `pytest` di komputer sendirilah yang dipakai sebagai bukti.





