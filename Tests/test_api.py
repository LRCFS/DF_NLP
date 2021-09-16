"""Tests the api.py functions"""

import xml.etree.ElementTree as ET
from unittest import mock
import pytest
from DF_NLP import api

ns = "{http://www.elsevier.com/xml/common/dtd}"


def test_process_def_list_elsevier():
    """Test the processing of Elsevier def-list"""
    long_string = (
        '<test xmlns:ce="http://www.elsevier.com/xml/common/dtd">' +
        '<ce:def-list><ce:def-term>Test</ce:def-term><ce:def-description>' +
        'Lorem ipsum</ce:def-description></ce:def-list></test>')

    root = ET.fromstring(long_string)
    root = root.find(f".//{ns}def-list")

    assert api._process_def_list(root, "") == "\n- Test: Lorem ipsum"


def test_process_def_list():
    """Test the processing of Springer or IEEE def-list"""
    long_string = (
        "<test><def-list><def-item><term>Test</term><def><p>Lorem ipsum</p>" +
        "</def></def-item></def-list></test>")

    root = ET.fromstring(long_string)
    root = root.find(".//def-list")

    assert api._process_def_list(root, "") == "- Test: Lorem ipsum"


def test_process_def_list_error():
    """Test the exception raising for _process_def_list()"""
    root = ET.fromstring("<test><def-list><wrong/></def-list></test>")
    root = root.find(".//def-list")

    with pytest.raises(ValueError):
        api._process_def_list(root, "")


def test_process_paragraph_elsevier(monkeypatch):
    """Test the processing of Elsevier paragraphs"""
    def mockreturn(element, text):
        return f"{text} [def-list]"

    long_string = (
        '<test xmlns:ce="http://www.elsevier.com/xml/common/dtd">' +
        '<ce:para>Lorem ipsum<ce:label>Label</ce:label><ce:list><item>' +
        '<ce:para>List_item1</ce:para></item><item><ce:para>List_item2' +
        '</ce:para></item></ce:list><ce:def-list></ce:def-list>' +
        '<ce:section-title>Title</ce:section-title><ce:para>Lorem ipsum' +
        '</ce:para></ce:para></test>')
    a = 'Lorem ipsum- List_item1 - List_item2 [def-list] Title Lorem ipsum '
    root = ET.fromstring(long_string)
    root = root.find(f".//{ns}para")
    monkeypatch.setattr(api, "_process_def_list", mockreturn)
    assert api._process_paragraph(root, "") == a


def test_process_paragraph(monkeypatch):
    """Test the processing of Springler and IEEE paragraphs"""
    def mockreturn(element, text):
        return f"{text} [def-list]"

    long_string = (
        "<test><p>Lorem ipsum<label>Label</label><list><item><p>List_item1" +
        "</p></item><item><p>List_item2</p></item></list><def-list>" +
        "</def-list><title>Title</title><p>Lorem ipsum</p></p></test>")
    a = 'Lorem ipsum- List_item1 - List_item2 [def-list] Title Lorem ipsum '
    root = ET.fromstring(long_string)
    root = root.find(".//p")
    monkeypatch.setattr(api, "_process_def_list", mockreturn)
    assert api._process_paragraph(root, "") == a


def test_process_paragraph_error():
    """Test the exception raising for _process_paragraph()"""
    root = ET.fromstring("<test><p>Lorem ipsum<wrong/></p></test>")
    root = root.find(".//p")

    with pytest.raises(ValueError):
        api._process_paragraph(root, "")


def test_process_section_elsevier(monkeypatch):
    """Test the processing of Elsevier sections"""
    def mockreturn(element, text):
        return f"{text} [Paragraph]"

    long_string = (
        '<test xmlns:ce="http://www.elsevier.com/xml/common/dtd">' +
        '<ce:sections><ce:section><ce:section-title>Title</ce:section-title>' +
        '<ce:label>Label</ce:label><ce:para></ce:para></ce:section>' +
        '</ce:sections></test>')
    root = ET.fromstring(long_string)
    root = root.find(f".//{ns}sections")
    monkeypatch.setattr(api, "_process_paragraph", mockreturn)
    assert api._process_section(root, "") == "Title\n [Paragraph]\n"


def test_process_section(monkeypatch):
    """Test the processing of Springer or IEEE sections"""
    def mockreturn(element, text):
        return f"{text} [Paragraph]"

    long_string = (
        "<test><body><sec><title>Title</title><label>Label</label><p></p>" +
        "</sec></body></test>"
    )
    root = ET.fromstring(long_string)
    root = root.find(".//body")
    monkeypatch.setattr(api, "_process_paragraph", mockreturn)
    assert api._process_section(root, "") == "Title\n [Paragraph]\n"


def test_process_section_error():
    """Test the exception raising for _process_section()"""
    root = ET.fromstring("<test><body><wrong/></body></test>")
    root = root.find(".//body")

    with pytest.raises(ValueError):
        api._process_section(root, "")


def test_process_elsevier():
    """Test the processing of Elsevier articles"""
    long_string = (
        '<test xmlns:ce="http://www.elsevier.com/xml/common/dtd">' +
        '<ce:sections><ce:section></ce:section><ce:para></ce:para>' +
        '</ce:sections></test>'
    )

    with mock.patch("builtins.open", mock.mock_open()):
        assert api.process(long_string, "", "elsevier") is None


@pytest.mark.parametrize("api_name", [
    "springer",
    "ieee"
])
def test_process(api_name):
    """Test the processing of Springer or IEEE articles"""
    long_string = "<test><body><sec></sec><p></p></body></test>"

    with mock.patch("builtins.open", mock.mock_open()):
        assert api.process(long_string, "", api_name) is None


def test_process_wrong_api():
    """Test the exception raising if a wrong API name is given"""
    long_string = "<test><body><sec></sec><p></p></body></test>"

    with mock.patch("builtins.open", mock.mock_open()):
        with pytest.raises(ValueError):
            assert api.process(long_string, "", "wrong")


@pytest.mark.parametrize("answer", [
    "<test></test>",
    "<test><body><book-part/></body></test>"
])
def test_process_no_full_text(answer):
    """Test the exception raising if there is no full text available"""
    with mock.patch("builtins.open", mock.mock_open()):
        with pytest.raises(NameError):
            assert api.process(answer, "", "springer")


def test_process_error():
    """Test the exception raising for process()"""
    with pytest.raises(ValueError):
        api.process("<test><body><wrong/></body></test>", "", "springer")


def test_get_elsevier_abstract():
    """Test the extraction of Elsevier abstract"""
    long_string = (
        '<test xmlns:dc="http://purl.org/dc/elements/1.1/">' +
        '<dc:description>Lorem ipsum</dc:description></test>'
    )

    assert api.get_elsevier_abstract(long_string) == "Lorem ipsum"


def test_get_springer_abstract():
    """Test the extraction of Springer abstract"""
    long_string = (
        "<test><abstract><title>Title</title><sec><p>Lorem ipsum sec</p>" +
        "</sec><p>Lorem ipsum p</p></abstract></test>"
    )

    assert api.get_springer_abstract(long_string
                                     ) == "Lorem ipsum sec Lorem ipsum p"


def test_get_springer_abstract_error():
    """Test the exception raising of Springer abstract"""
    with pytest.raises(ValueError):
        api.get_springer_abstract("<test><abstract><wrong/></abstract></test>")


def test_get_ieee_abstract():
    """Test the extraction of IEEE abstract"""
    long_string = (
        "<test><article><abstract>Lorem ipsum</abstract></article></test>"
    )

    assert api.get_ieee_abstract(long_string) == "Lorem ipsum"


def test_get_ieee_abstract_empty():
    """Test the default value of IEEE abstract"""
    assert not api.get_ieee_abstract("<test><article></article></test>")
