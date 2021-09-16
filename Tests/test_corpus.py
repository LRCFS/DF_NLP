"""Tests the corpus.py functions"""

import json
from unittest import mock

import pytest
from DF_NLP import corpus, query

import fixture


def test_search_doi_doi():
    """Test if _search_doi() handle DOI category"""
    assert corpus._search_doi({"DOI": "0-1/(test).23"}) == "0-1/(test).23"


@pytest.mark.parametrize("d", [
    {"note": "DOI: 0-1/(test).23"},
    {"note": "DOI: 0-1/(test).23, Misc: lorem ipsum"},
    {"note": "Misc: lorem ipsum, DOI: 0-1/(test).23"},
    {"note": "Misc: lorem ipsum, DOI: 0-1/(test).23, Misc: lorem ipsum"}
])
def test_search_doi_note(d):
    """Test if _search_doi() handle note category"""
    assert corpus._search_doi(d) == "0-1/(test).23"


@pytest.mark.parametrize("d", [
    {},
    {"Title": "lorem ipsum"},
    {"doi": "lorem ipsum"},
    {"DOI": ""},
    {"note": ""},
    {"NOTE": "DOI: 0-1/(test).23"},
    {"note": "Misc: lorem ipsum"},
    {"note": "doi: lorem ipsum"},
    {"note": "DOI:lorem ipsum"}
])
def test_search_doi_empty(d):
    """Test if _search_doi() handle dict without DOI"""
    assert not corpus._search_doi(d)


def test_search_author_author():
    """Test if _search_author() handle author category"""
    d = {
        "author": [
            {"given": "John", "family": "Doe"},
            {"given": "Jane", "family": "Doe"}],
        "editor": [{"given": "John", "family": "Smith"}]
    }

    assert corpus._search_author(d) == "John Doe, Jane Doe"


def test_search_author_editor():
    """Test if _search_author() handle editor category"""
    d = {"editor": [{"given": "John", "family": "Smith"}]}

    assert corpus._search_author(d) == "(Ed.) John Smith"


@pytest.mark.parametrize("d", [
    {},
    {"Title": "lorem ipsum"},
    {"AUTHOR": [{"given": "John", "family": "Smith"}]},
    {"author": [], "EDITOR": [{"given": "John", "family": "Smith"}]},
    {"author": []},
    {"author": [], "editor": []}
])
def test_search_author_empty(d):
    """Test if _search_author() handle dict without authors"""
    assert not corpus._search_author(d)


def test_search_source_container():
    """Test if _search_source() handle container-title category"""
    assert corpus._search_source({"container-title": "test"}) == "test"


@pytest.mark.parametrize("d", [
    {"note": "container-title: test.-()"},
    {"note": "container-title: test.-(), Misc: lorem ipsum"},
    {"note": "Misc: lorem ipsum, container-title: test.-()"},
    {"note": "Misc: lorem ipsum, container-title: test.-(), Misc: lorem ipsum"}
])
def test_search_source_note(d):
    """Test if _search_source() handle note category"""
    assert corpus._search_source(d) == "test.-()"


def test_search_source_event():
    """Test if _search_source() handle event category"""
    d = {
        "type": "paper-conference",
        "event": "test"
    }
    assert corpus._search_source(d) == "test"


@pytest.mark.parametrize("d", [
    {},
    {"Title": "lorem ipsum"},
    {"CONTAINER-TITLE": "lorem ipsum"},
    {"NOTE": "container-title: lorem ipsum"},
    {"TYPE": "lorem ipsum"},
    {"containter-title": ""},
    {"note": ""},
    {"type": ""},
    {"type": "lorem ipsum"},
    {"note": "Misc: lorem ipsum"},
    {"note": "CONTAINER-TITLE: lorem ipsum"},
    {"note": "container-title:lorem ipsum"}
])
def test_search_source_empty(d):
    """Test if _search_source() handle dict without source"""
    assert not corpus._search_doi(d)


@pytest.mark.parametrize("d", [
    {"date-parts": [["2021", "1", "1"]]},
    {"date-parts": [["2021"]]},
    {"date-parts": [[2021, 1, 1]]},
    {"date-parts": [[2021]]}
])
def test_search_year(d):
    """Test if _search_year() find the year"""
    assert corpus._search_year(d) == "2021"


@pytest.mark.parametrize("d", [
    {},
    {"date-parts": [["1", "12"]]},
    {"date-parts": [[1, 12]]},
    {"date-parts": [[]]}
])
def test_search_year_empty(d):
    """Test if _search_year() handle dict without year"""
    assert not corpus._search_year(d)


@pytest.mark.usefixtures("raw_corpus", "extracted_corpus")
def test_extract(raw_corpus, extracted_corpus):
    """Test the behaviour of extract()"""
    mock_open = mock.mock_open(read_data=raw_corpus)
    with mock.patch("builtins.open", mock_open):
        assert json.dumps(corpus.extract("")) == extracted_corpus


def test_generate_filename():
    """Test the behaviour of _generate_filename()"""
    assert corpus._generate_filename(
        "http://zotero.org/users/local/uuid1a/items/uuid1b",
        "~/") == "~/uuid1a_uuid1b.txt"


def test_unknown_publisher_elsevier(monkeypatch):
    """Test if _unknown_publisher() recognizes Elsevier references"""
    def mockreturn(doi, key):
        return "test"

    monkeypatch.setattr(query, "elsevier_get", mockreturn)
    assert corpus._unknown_publisher("uuid", {})[1] == "elsevier"


@pytest.mark.parametrize("answer", [
    "<test><body>lorem ipsum</body></test>",
    "<test><abstract>lorem ipsum</abstract></test>",
    "<test><body>lorem ipsum</body><abstract>lorem ipsum</abstract></test>"
])
def test_unknown_publisher_springer(monkeypatch, answer):
    """Test if _unkown_publisher() recognizes Springer references"""
    def mockreturn(doi, key):
        return answer

    monkeypatch.setattr(query, "springer_get", mockreturn)
    assert corpus._unknown_publisher("uuid", {})[1] == "springer"


def test_unknown_publisher_unknown(monkeypatch):
    """Test if _unknown_publisher() handle unknown references"""
    def mockreturn(doi, key):
        return "<test></test>"

    monkeypatch.setattr(query, "springer_get", mockreturn)
    assert corpus._unknown_publisher("uuid", {}) == (None, None, None)
