#! usr/bin/env python3
"""Module setting up the corpus using a CLS JSON bibliography."""

import json
import re
import sys
from typing import Dict, List

from tqdm import tqdm

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
        pattern = re.compile(r"(?<=DOI: )[-\w./]+")
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


if __name__ == "__main__":
    # Test the number of arguments
    if len(sys.argv) != 2:
        print("This script needs only one argument!\n"
              + "Usage: ./corpus.py input_path")
        sys.exit(1)

    corpus = extract(sys.argv[1])
