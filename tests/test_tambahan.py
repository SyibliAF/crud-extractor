"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import LexError, TokenType as T, tokenize


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