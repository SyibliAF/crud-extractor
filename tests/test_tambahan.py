"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import LexError, TokenType as T, tokenize
from crud.analyzer import analyze_statement
from crud.parser import parse_sql
from crud.resolver import Resolver
from crud import ast_nodes as ast


#TEST REGRESI BIASA

# --- lexer ---
def test_regresi_komentar_blok_berisi_bintang():
    toks = tokenize("/* a * b */ SELECT")
    assert toks[0].value == "SELECT"
 
 
def test_regresi_komentar_blok_lintas_baris_menjaga_nomor_baris():
    toks = tokenize("/* a\n b */ SELECT")
    assert (toks[0].value, toks[0].line) == ("SELECT", 2)
 
 
def test_regresi_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError):
        tokenize("SELECT /* belum ditutup")
 
 
def test_regresi_keyword_campuran_huruf_dinormalisasi():
    toks = tokenize("Select selection")
    assert (toks[0].type, toks[0].value) == (T.KEYWORD, "SELECT")
    assert toks[1].type == T.IDENT
 
 
def test_regresi_operator_tidak_sama_dengan_satu_token():
    vals = [t.value for t in tokenize("a <> 1") if t.type != T.EOF]
    assert vals == ["a", "<>", "1"]
 
 
def test_regresi_kutip_ganda_dalam_string_jadi_satu_token():
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"
    assert toks[1].type == T.EOF
 
 
# --- parser ---
def test_regresi_and_lebih_kuat_dari_or():
    where = parse_sql("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;").statements[0].where
    assert where.op == "OR"
    assert where.right.op == "AND"
 
 
def test_regresi_recovery_berhenti_di_titik_koma():
    script = parse_sql("SELECT id nama, FROM x;\nDELETE FROM y WHERE id = 1;")
    assert len(script.errors) == 1
    assert len(script.statements) == 1
    assert type(script.statements[0]).__name__ == "Delete"
 
 
def test_regresi_left_outer_join():
    script = parse_sql("SELECT * FROM a LEFT OUTER JOIN b ON a.x = b.x;")
    assert script.errors == []
    assert script.statements[0].joins[0].kind == "LEFT"
 
 
def test_regresi_insert_select():
    script = parse_sql("INSERT INTO arsip (id) SELECT id FROM pesanan;")
    assert script.errors == []
    stmt = script.statements[0]
    assert stmt.table.name == "arsip"
    assert stmt.columns == ["id"]
    assert stmt.values == []
    assert type(stmt.query).__name__ == "Select"
 
 
#TEST TEPI
def test_tepi_script_tanpa_statement():
    # Berisiko: loop parser bisa salah menangani script tanpa satu pun statement
    # (kosong, hanya titik koma, atau hanya komentar).
    for sumber in ["", ";;;", "-- hanya komentar", "/* hanya komentar */"]:
        script = parse_sql(sumber)
        assert script.statements == []
        assert script.errors == []
 
 
def test_tepi_and_milik_between_tidak_dianggap_operator_logika():
    # Berisiko: AND punya dua arti; yang pertama milik BETWEEN, yang kedua operator logika.
    where = parse_sql("SELECT a FROM t WHERE x BETWEEN 1 AND 2 AND y = 3;").statements[0].where
    assert where.op == "AND"
    assert type(where.left).__name__ == "Between"
    assert where.right.op == "="
 
 
def test_tepi_string_kosong_dan_string_berakhir_kutip_escape():
    # Berisiko: aturan '' bertabrakan dengan string kosong dan dengan '' tepat sebelum
    # kutip penutup. '' adalah string kosong, 'a''' adalah string bernilai a'.
    kosong = tokenize("''")
    assert (kosong[0].type, kosong[0].value) == (T.STRING, "")
    berakhir_escape = tokenize("'a'''")
    assert (berakhir_escape[0].type, berakhir_escape[0].value) == (T.STRING, "a'")
 
 
def test_tepi_string_tidak_ditutup_melaporkan_posisi_pembuka():
    # Berisiko: string yang membentang beberapa baris tanpa penutup; posisi error
    # harus menunjuk kutip pembukanya (baris 1, kolom 8), bukan akhir input.
    with pytest.raises(LexError) as info:
        tokenize("SELECT 'belum\ntutup")
    assert (info.value.line, info.value.col) == (1, 8)
        
        
#analyzer.py
def crud(sql):
    # Parse satu statement, pastikan tidak ada error sintaks, lalu hitung CRUD-nya.
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return analyze_statement(script.statements[0])

def test_regresi_update_subquery_di_where_dan_set_hanya_membaca():
    # Tabel yang dibaca lewat subquery harus R, apa pun jenis statement luarnya. Hanya target UPDATE yang U.
    assert crud("UPDATE pelanggan SET level = 'gold' "
                "WHERE id IN (SELECT pelanggan_id FROM pesanan)") == {
        "pelanggan": {"U"}, "pesanan": {"R"}}
    assert crud("UPDATE pelanggan SET total = (SELECT SUM(total) FROM pesanan)") == {
        "pelanggan": {"U"}, "pesanan": {"R"}}
    
    
#resolver.py
def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    diagnostics = Resolver().resolve_script(script)
    return script, diagnostics
def columns(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


def test_kolom_tanpa_qualifier_dua_tabel():
    # Dua tabel di scope terdalam
    script, diags = resolve("SELECT nama FROM pelanggan, pemesan WHERE aktif = 1")
    assert [c.resolved for c in columns(script)] == [None, None]
    assert [d.level for d in diags] == ["warning", "warning"]
    assert "ambigu" in diags[0].message and "'nama'" in diags[0].message


def test_kolom_tanpa_qualifier_tanpa_tabel():
    # INSERT tidak membuat scope table
    script, diags = resolve("INSERT INTO pelanggan VALUES (nama)")
    assert [c.resolved for c in columns(script)] == [None]
    assert [d.level for d in diags] == ["warning"]
    
def test_regresi_alias_subquery_menutupi_alias_luar():
    # qualifier harus dicari dari scope terdalam ke luar
    script, diags = resolve(
        "SELECT p.a FROM pelanggan p "
        "WHERE EXISTS (SELECT 1 FROM pesanan p WHERE p.id = 1)")
    resolved = {c.name: c.resolved for c in columns(script)}
    assert resolved["a"] == "pelanggan"
    assert resolved["id"] == "pesanan"
    assert diags == []


def test_regresi_alias_delete_tidak_bocor_ke_statement_berikutnya():
    # Tiap statement berdiri sendiri
    script = parse_sql("DELETE FROM pesanan o WHERE id = 1; SELECT o.id FROM pelanggan")
    assert script.errors == []
    resolver = Resolver()
    diags = resolver.resolve_script(script)
    assert [d.level for d in diags] == ["error"]
    assert "'o'" in diags[0].message
    assert [c.resolved for c in columns(script.statements[1])] == [None]
    assert resolver.scope is None