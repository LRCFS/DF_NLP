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

from DF_NLP import spacy_update


def setup_spacy():
    """Setup the SpaCy model used to process text.

    Returns:
        Spacy English model.
    """
    # Load model
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    # Update the list of stop words
    nlp.Defaults.stop_words |= spacy_update.SCI_PAPER_STOP
    nlp.Defaults.stop_words |= spacy_update.DIGTAL_FORENSICS_STOP
    # Update lemmatization rules
    lookup = nlp.get_pipe("lemmatizer").lookups
    lookup.get_table("lemma_exc")["noun"].pop("data")

    return nlp


def text_process(nlp, text: str) -> str:
    """Override the SpaCy part of PyATE to process text.

    Args:
        nlp: English model of SpaCy.
        text: Text to process.

    Returns:
        Lemmatized text without stopwords.
    """
    # Transform the string into a Doc
    doc = nlp(text)
    # Lemmatized text
    doc = nlp(" ".join(tok.lemma_ for tok in doc if not tok.is_punct))
    # Remove stopwords
    doc = " ".join(tok.text for tok in doc if not tok.is_stop)

    return doc.lower()


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
    nlp = setup_spacy()

    for ref in tqdm(corpus.values()):
        if ref.get("full_text"):
            with open(ref.get("full_text"), "r") as f:
                doc = text_process(nlp, f.read())
            text.append(doc)
        elif ref.get("abstract"):
            doc = text_process(nlp, ref.get("abstract"))
            text.append(doc)

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
    if method == "Basic":
        res = basic(corpus, have_single_word=single,
                    verbose=True).sort_values(ascending=False)
    elif method == "Combo":
        res = combo_basic(corpus, have_single_word=single,
                          verbose=True).sort_values(ascending=False)
    elif method == "Cvalue":
        res = cvalues(corpus, have_single_word=single,
                      verbose=True).sort_values(ascending=False)
    elif method == "Weirdness":
        general = TermExtraction.get_general_domain()
        res = weirdness(corpus, general,
                        verbose=True).sort_values(ascending=False)

    return res[res > 0.0]


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("corpus_path", type=str, help="Path to the corpus file")
    cli.add_argument("output", type=str, help="Path to the output directory")
    cli.add_argument("--ate", nargs="*", type=str, default=["Weirdness"],
                     choices=["Basic", "Combo", "Cvalue", "Weirdness"],
                     help="ATE methods to use")

    args = cli.parse_args()

    corpus = read_corpus(args.corpus_path)
    for ate in args.ate:
        candidates = run_ate(ate, True, corpus)
        filename = os.path.join(args.output, f"{ate}.csv")
        candidates.to_csv(filename, sep=";", index=True)
