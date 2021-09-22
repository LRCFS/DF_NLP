#!/usr/bin/env python
"""Launch ATE methods on the digital forensics corpus."""

import argparse
import json
import os
import re
from typing import List

import pandas as pd
import spacy
from pyate import TermExtraction, basic, combo_basic, cvalues, weirdness
from tqdm import tqdm


def read_corpus(corpus_path: str) -> List[str]:
    """Extract abstract or, when possible, full text from the corpus.

    Args:
        corpus_path: Path to the corpus.

    Returns:
        List of strings
    """
    with open(corpus_path, "r") as f:
        corpus = json.load(f)

    text = []

    for ref in corpus.values():
        if ref.get("full_text"):
            with open(ref.get("full_text"), "r") as f:
                text.append(f.read())
        elif ref.get("abstract"):
            text.append(ref.get("abstract"))

    return text


def run_ate(method: str, single: bool, corpus: List[str]) -> pd.Series:
    """Run an ATE method against the given corpus.

    Args:
        method: Name of the ATE method to use.
        single: Weither or not retrieving single word as candidates.
        corpus: Corpus to analyze.

    Returns:
        Candidate terms and their scores.

    Raises:
        ValueError: The value of `method` is not handled
    """
    nlp = spacy.load("en_core_web_sm")

    text = []
    for doc in tqdm(list(nlp.pipe(corpus))):
        doc = " ".join(token.lemma_ for token in doc)
        doc = re.sub(r' (?=\W)', "", doc)
        doc = re.sub("- ", "-", doc)
        text.append(doc)

    if method == "Basic":
        res = basic(text, have_single_word=single,
                    verbose=True).sort_values(ascending=False)
    elif method == "Combo":
        res = combo_basic(text, have_single_word=single,
                          verbose=True).sort_values(ascending=False)
    elif method == "Cvalue":
        res = cvalues(text, have_single_word=single,
                      verbose=True).sort_values(ascending=False)
    elif method == "Weirdness":
        general = TermExtraction.get_general_domain()
        res = weirdness(text, general,
                        verbose=True).sort_values(ascending=False)

    return res[res > 0.0]


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("corpus_path", type=str, help="Path to the corpus file")
    cli.add_argument("output", type=str, help="Path to the output directory")
    cli.add_argument("--ate", nargs="*", type=str, default=["Weirdness"],
                     choices=["Basic", "Combo", "Cvalues", "Weirdness"],
                     help="ATE methods to use")

    args = cli.parse_args()

    corpus = read_corpus(args.corpus_path)
    for ate in args.ate:
        candidates = run_ate(ate, True, corpus)
        filename = os.path.join(args.output, f"{ate}.csv")
        candidates.to_csv(filename, sep=";", index=True)
