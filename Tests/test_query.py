"""Tests the query.py functions"""

from unittest import mock

import pytest
import requests
from DF_NLP import query

import fixture


def mockget(q):
    r = requests.models.Response()
    r.status_code = 200
    return r


def test_get_correct(monkeypatch):
    """Test the behaviour _get() when a correct answer is returned"""
    monkeypatch.setattr(requests, "get", mockget)
    answer = query._get("test")
    assert answer.status_code == 200 and not answer.content


def test_get_incorrect():
    """Test the exception raising by _get() with an incorrect query"""
    with pytest.raises(Exception):
        query._get("test")


@pytest.mark.parametrize("function", [
    query.elsevier_get,
    query.ieee_get_meta
])
def test_elsevier_ieee_meta_get_correct(monkeypatch, function):
    """Test elsevier_get() and ieee_get_meta() for a correct answer"""
    monkeypatch.setattr(requests, "get", mockget)
    monkeypatch.setattr(requests.models.Response, "content", b"lorem ipsum")
    assert query.elsevier_get("test", "") == "lorem ipsum"


def test_elsevier_get_incorrect():
    """Test the exception raising by elsevier_get() with an incorrect query"""
    with pytest.raises(Exception):
        query.elsevier_get("test", "")


@pytest.mark.parametrize("answer", [
    b"<test><result><total>0</total></result></test>",
    b"<test><result><total>1</total></result></test>"
])
def test_springer_get_correct(monkeypatch, answer):
    """Test springer_get() behaviour with a correct answer"""
    monkeypatch.setattr(requests, "get", mockget)
    monkeypatch.setattr(requests.models.Response, "content", answer)
    assert query.springer_get("test", "") == answer.decode("UTF-8")


def test_ieee_get_oa(monkeypatch):
    """Test ieee_get_oa() behaviour with a correct answer"""
    meta = "<t><article><article_number>1</article_number></article></t>"
    monkeypatch.setattr(requests, "get", mockget)
    monkeypatch.setattr(requests.models.Response, "content", b"lorem ipsum")
    assert query.ieee_get_oa(meta, "") == "lorem ipsum"


def test_api_keys_correct(monkeypatch):
    """Test api_keys() behaviour when all API are up"""
    def mockapi(doi, key):
        return ""

    monkeypatch.setattr(query, "elsevier_get", mockapi)
    monkeypatch.setattr(query, "springer_get", mockapi)
    monkeypatch.setattr(query, "ieee_get_meta", mockapi)

    keys = '{"elsevier": "1", "springer": "2", "ieee": "3"}'
    mock_open = mock.mock_open(read_data=keys)
    with mock.patch("builtins.open", mock_open):
        assert query.api_keys("") == eval(keys)


def test_api_keys_incorrect_elsevier(monkeypatch):
    """Test api_keys() behaviour when issue with Elsevier"""
    def mockapi(doi, key):
        return ""

    monkeypatch.setattr(query, "springer_get", mockapi)
    monkeypatch.setattr(query, "ieee_get_meta", mockapi)

    keys = '{"elsevier": "1", "springer": "2", "ieee": "3"}'
    mock_open = mock.mock_open(read_data=keys)
    with mock.patch("builtins.open", mock_open):
        with pytest.raises(SystemExit):
            query.api_keys("")


def test_api_keys_incorrect_springer(monkeypatch):
    """Test api_keys() behaviour when issue with Springer"""
    def mockapi(doi, key):
        return ""

    monkeypatch.setattr(query, "elsevier_get", mockapi)
    monkeypatch.setattr(query, "ieee_get_meta", mockapi)

    keys = '{"elsevier": "1", "springer": "2", "ieee": "3"}'
    mock_open = mock.mock_open(read_data=keys)
    with mock.patch("builtins.open", mock_open):
        with pytest.raises(SystemExit):
            query.api_keys("")


def test_api_keys_incorrect_ieee(monkeypatch):
    """Test api_keys() behaviour when issue with IEEE"""
    def mockapi(doi, key):
        return ""

    monkeypatch.setattr(query, "elsevier_get", mockapi)
    monkeypatch.setattr(query, "springer_get", mockapi)

    keys = '{"elsevier": "1", "springer": "2", "ieee": "3"}'
    mock_open = mock.mock_open(read_data=keys)
    with mock.patch("builtins.open", mock_open):
        with pytest.raises(SystemExit):
            query.api_keys("")
