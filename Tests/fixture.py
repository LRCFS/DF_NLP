import pytest
import json
import xml.etree.ElementTree as ET


@pytest.fixture
def raw_corpus():
    obj = [
        {
            "id": "http://zotero.org/users/local/uuid1/items/uuid1",
            "DOI": "12.345/678-(9)",
            "ISBN": "lorem ipsum isbn",
            "ISSN": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": [{"given": "Jane", "family": "Doe"}],
            "container-title": "lorem ipsum source",
            "issued": {"date-parts": [[2021]]},
            "publisher": "lorem ipsum publisher",
            "URL": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        {
            "id": "http://zotero.org/users/local/uuid2/items/uuid2",
            "ISBN": "lorem ipsum isbn",
            "ISSN": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "editor": [{"given": "Jane", "family": "Doe"}],
            "note": "container-title: lorem ipsum source, DOI: 987.654/32-(1)",
            "issued": {"date-parts": [[]]},
            "publisher": "elsevier",
            "URL": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        {
            "id": "http://zotero.org/users/local/uuid3/items/uuid3",
            "DOI": "12.345/678-(9)",
            "ISBN": "lorem ipsum isbn",
            "ISSN": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": [{"given": "Jane", "family": "Doe"}],
            "container-title": "lorem ipsum source IEEE",
            "issued": {"date-parts": [[2021]]},
            "publisher": "lorem ipsum publisher",
            "URL": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        {
            "id": "http://zotero.org/users/local/uuid4/items/uuid4",
            "ISBN": "lorem ipsum isbn",
            "ISSN": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "editor": [{"given": "Jane", "family": "Doe"}],
            "note": "container-title: lorem ipsum source, DOI: 987.654/32-(1)",
            "issued": {"date-parts": [[]]},
            "publisher": "Springer",
            "URL": "lorem ipsum url",
            "abstract": "",
        }
    ]

    return json.dumps(obj)


@pytest.fixture
def extracted_corpus():
    obj = {
        "http://zotero.org/users/local/uuid1/items/uuid1": {
            "doi": "12.345/678-(9)",
            "isbn": "lorem ipsum isbn",
            "issn": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": "Jane Doe",
            "source": "lorem ipsum source",
            "year": "2021",
            "publisher": "lorem ipsum publisher",
            "url": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        "http://zotero.org/users/local/uuid2/items/uuid2": {
            "doi": "987.654/32-(1)",
            "isbn": "lorem ipsum isbn",
            "issn": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": "(Ed.) Jane Doe",
            "source": "lorem ipsum source",
            "year": "",
            "publisher": "elsevier",
            "url": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        "http://zotero.org/users/local/uuid3/items/uuid3": {
            "doi": "12.345/678-(9)",
            "isbn": "lorem ipsum isbn",
            "issn": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": "Jane Doe",
            "source": "lorem ipsum source IEEE",
            "year": "2021",
            "publisher": "lorem ipsum publisher",
            "url": "lorem ipsum url",
            "abstract": "lorem ipsum abstract",
        },
        "http://zotero.org/users/local/uuid4/items/uuid4": {
            "doi": "987.654/32-(1)",
            "isbn": "lorem ipsum isbn",
            "issn": "lorem ipsum issn",
            "type": "lorem ipsum type",
            "title": "lorem ipsum title",
            "author": "(Ed.) Jane Doe",
            "source": "lorem ipsum source",
            "year": "",
            "publisher": "Springer",
            "url": "lorem ipsum url",
            "abstract": "",
        }
    }

    return json.dumps(obj)
