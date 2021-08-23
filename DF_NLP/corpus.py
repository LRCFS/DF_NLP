#!/usr/bin/env python3
"""Module setting up the corpus using a CLS JSON bibliography."""

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

import api
import query

Corpus = Dict[str, Dict[str, str]]


def _search_doi(ref: dict) -> str:
    """Search the DOI of the reference.

    Args:
        ref: Reference as a dictionnary.

    Returns:
        DOI as a string.
    """
    doi = str()

    if ref.get("DOI"):
        doi = ref.get("DOI")
    elif ref.get("note"):
        pattern = re.compile(r"(?<=DOI: )[-\w./\(\)]+")
        res = pattern.search(ref.get("note"))
        if res:
            doi = res.group()

    return doi


def _search_author(ref: dict) -> str:
    """Search the author(s) (or editor(s)) of the reference.

    Args:
        ref: Reference as a dictionnary.

    Returns:
        Author(s) (or editor(s)) as a string.
    """
    people = str()

    if ref.get("author"):
        name_list = [f"{p.get('given')} {p.get('family')}"
                     for p in ref.get("author")]
        people = ", ".join(name_list)
    elif ref.get("editor"):
        name_list = [f"{p.get('given')} {p.get('family')}"
                     for p in ref.get("editor")]
        people = f"(Ed.) {', '.join(name_list)}"

    return people


def _search_source(ref: dict) -> str:
    """Search the source (document or event) of the reference.

    Args:
        ref: Reference as a dictionnary.

    Returns:
        Source (document or event) of the reference as a string.
    """
    source = str()

    if ref.get("container-title"):
        source = ref.get("container-title")
    elif ref.get("note"):
        pattern = re.compile(r"(?<=container-title: )[- \w./()]+")
        res = pattern.search(ref.get("note"))
        if res:
            source = res.group()
    elif ref.get("type") == "paper-conference":
        source = ref["event"]

    return source


def _search_year(date: dict) -> str:
    """Search the issued year of the reference.

    Args:
        date: Dictionnary containing issued date of the reference.

    Returns:
        Issued year of the reference as a string.
    """
    year = []

    if date:
        date = [str(i) for i in date.get("date-parts")[0]]
        pattern = re.compile(r"\d{4}")
        year = list(filter(pattern.match, date))

    return year[0] if year else ""


def extract(json_path: str) -> Corpus:
    """Read a CLS JSON bibliography file and extract references.

    Args:
        json_path: Path to the CLS JSON file.

    Returns:
        A dictionnary with UUID as key and reference information as value.
    """
    with open(json_path, "r") as f:
        raw = json.load(f)

    # UUID are keys of the dictionnary and information of the UUID-related
    # reference are the values.
    return {ref.get("id"): {
        "doi": _search_doi(ref),
        "isbn": ref.get("ISBN", ""),
        "issn": ref.get("ISSN", ""),
        "type": ref.get("type", ""),
        "title": ref.get("title", ""),
        "author": _search_author(ref),
        "source": _search_source(ref),
        "year": _search_year(ref.get("issued")),
        "publisher": ref.get("publisher", ""),
        "url": ref.get("URL", ""),
        "abstract": ref.get("abstract", "")
    } for ref in tqdm(raw)}


def summary(corpus: Corpus) -> None:
    """Print quantitative information about `corpus`.

    Args:
        corpus: Corpus of references.
    """
    s = {
        "total": len(corpus),
        "abstract": 0,
        "p_abstract": 0.0,
        "text": 0,
        "p_text": 0.0
    }

    for v in corpus.values():
        if v.get("abstract", ""):
            s["abstract"] += 1
        if v.get("full_text", ""):
            s["text"] += 1

    s["p_abstract"] = 100 * (s.get("abstract") / s.get("total"))
    s["p_text"] = 100 * (s.get("text") / s.get("total"))

    long_str = ("\n=============== Summary ===============\n\n"
                + f"Total of references: {s.get('total')}\n"
                + f"References with abstract: {s.get('abstract')}"
                + f" ({round(s.get('p_abstract'), 2)}%)\n"
                + f"References with full text: {s.get('text')}"
                + f" ({round(s.get('p_text'), 2)}%)\n\n"
                + "=======================================")

    print(long_str)


def _generate_filename(uuid: str, dirpath: str) -> str:
    """Generate a unique filename to save the full text of a reference.

    Args:
        uuid: UUID of the reference.
        dirpath: Directory path where to save the full text references.

    Returns:
        A unique filename.
    """
    uuid = re.sub("http://zotero.org/users/local/", "", uuid)
    uuid = re.sub("/items/", "_", uuid)
    filename = os.path.join(dirpath, f"{uuid}.txt")

    return filename


def search(corpus: Corpus, api_keys_path: str, dirpath: str) -> None:
    """Query provider API to retrieve full text of reference.

    Args:
        corpus: Corpus of references.
        api_keys_path: Path to the file containings API keys.
        dirpath: Path to the directory where the full text will be saved.
    """
    keys = query.api_keys(api_keys_path)

    for k, v in tqdm(corpus.items()):
        publisher = str.lower(v.get("publisher"))

        # Generate filename
        path = _generate_filename(k, dirpath)
        # Ignore existing files
        if os.path.exists(path):
            continue

        # Ignore references without DOI
        if not v.get("doi", ""):
            continue

        try:
            if "elsevier" in publisher:
                answer = query.elsevier_get(v.get("doi"), keys.get("elsevier"))
                api_name = "elsevier"
                abs_function = api.get_elsevier_abstract
            elif "springer" in publisher:
                answer = query.springer_get(v.get("doi"), keys.get("springer"))
                api_name = "springer"
                abs_function = api.get_springer_abstract
            elif "ieee" in publisher:
                meta = query.ieee_get_meta(v.get("doi"), keys.get("ieee"))
                api_name = "ieee"
                abs_function = api.get_ieee_abstract
                try:
                    answer = query.ieee_get_oa(meta, keys.get("ieee"))
                except Exception:
                    answer = meta
            else:
                continue
        except ValueError as e:
            print(e)
            raise ValueError(f"Error occured in the following reference:\n{k}")

        # Max 10 queries per second for IEEE API
        time.sleep(0.2)

        try:
            try:
                api.process(answer, path, api_name)
                v["full_text"] = path
            except NameError:
                if not v.get("abstract", ""):
                    v["abstract"] = abs_function(answer)
        except ValueError as e:
            print(e)
            raise ValueError(f"Error occured in the following reference:\n{k}")
        except ET.ParseError as e:
            print(e)
            raise ValueError(f"Error occured in the following reference:\n{k}")
        except TypeError as e:
            print(e)
            raise ValueError(f"Error occured in the following reference:\n{k}")


if __name__ == "__main__":
    # Test the number of arguments
    if len(sys.argv) != 4:
        print("This script needs only one argument!\n"
              + "Usage: ./corpus.py input_path output_path api_key_path")
        sys.exit(1)

    corpus = extract(sys.argv[1])
    summary(corpus)

    search(corpus, sys.argv[3], sys.argv[2])
    summary(corpus)

    json_obj = json.dumps(corpus)
    with open(os.path.join(sys.argv[2], "corpus.json"), "w") as f:
        f.write(json_obj)
