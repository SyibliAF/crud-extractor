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


def test_regresi_operator_tidak_sama_dengan_satu_token():
    vals = [t.value for t in tokenize("a <> 1") if t.type != T.EOF]
    assert vals == ["a", "<>", "1"]


def test_regresi_kutip_ganda_dalam_string_jadi_satu_token():
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"
    assert toks[1].type == T.EOF


def test_regresi_keyword_campuran_huruf_dinormalisasi():
    toks = tokenize("Select selection")
    assert (toks[0].type, toks[0].value) == (T.KEYWORD, "SELECT")
    assert toks[1].type == T.IDENT


def test_regresi_komentar_blok_berisi_bintang():
    toks = tokenize("/* a * b */ SELECT")
    assert toks[0].value == "SELECT"


def test_regresi_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError):
        tokenize("SELECT /* belum ditutup")
        
        
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