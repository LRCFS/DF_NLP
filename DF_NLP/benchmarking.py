#!/usr/bin/env python3
"""Benchmark several ATE method for the SemEval 2017 corpus."""

import os
from math import pow
from typing import Dict, List, Tuple
import re
import numpy as np
import pandas as pd
from pyate import TermExtraction, basic, combo_basic, cvalues, weirdness
from tqdm import tqdm


def read_files(directory: str) -> Tuple[List[str]]:
    """Extract files from the input `directory`.

    Args:
        directory: Path to the directory containing the files.

    Returns:
        Two dictionnaries, one containing the text contents and the
        other one containing the annotations.

    Raises:
        FileNotFoundError: If the given `directory` does not exists.
        SyntaxError: If a file is neither a .txt nor a .ann file.
    """
    # Check existence of the directory
    if not os.path.exists(directory):
        raise FileNotFoundError(f"No such directory: '{directory}'")

    # List all files from the directory
    file_list = [os.path.join(directory, f) for f in os.listdir(directory)]

    to_remove = dict.fromkeys((ord(c) for c in u"\xa0\n\t"))

    text = []
    df = pd.DataFrame(columns=["Type", "Info", "Term"])
    for f_name in tqdm(file_list):
        # Extract strings from the .txt files
        if f_name.endswith(".txt"):
            with open(f_name, "r") as f:
                tmp = f.read()
            text.append(tmp.translate(to_remove))
        # Extract annotation as DataFrame from the .ann files
        elif f_name.endswith(".ann"):
            tmp = pd.read_csv(f_name, header=0,
                              names=["Type", "Info", "Term"],
                              sep="\t", dtype=str)
            df = df.append(tmp, ignore_index=True)
        else:
            raise SyntaxError(f"Unhandled extension: {f_name}")

    # Remove row which are not terms and duplicates
    df = df.loc[df.loc[:, "Type"].str.startswith("T"), ]
    df = df.drop_duplicates("Term")

    annotation = df.loc[:, "Term"].str.lower().to_list()
    annotation = [a.translate(to_remove) for a in annotation]

    return (text, annotation)


def prf_score(candidate: List[str], annotation: List[str]) -> Dict[str, float]:
    """Method which compute the precision, recall and F-measure.

    Args:
        candidate: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.

    Returns:
        A dictionnary containing the precision, the recall and F-measure.
    """
    print("PRF scoring...")
    beta = 2
    match = sum(c in candidate for c in annotation)

    p = match / len(candidate)
    r = match / len(annotation)
    try:
        f = (1 + pow(beta, 2)) * (p*r / (pow(beta, 2)*p + r))
    except ZeroDivisionError:
        f = 0.0

    prf = {"Precision": p, "Recall": r, "F_Measure": f}
    print(prf)
    return prf


def benchmarck(text: List[str], annotation: List[str]) -> pd.DataFrame:
    """Benchmark of Basic, Combo Basic, C-Value and Weirdness ATE methods

    Args:
        text: The corpus used to compare the methods.
        annotation: The terms identified by authors in `text`.

    Returns:
        DataFrame containing precision, recall and F-measure for each
        method.
    """
    general = TermExtraction.get_general_domain()
    score = pd.DataFrame(
        columns=["Precision", "Recall", "F_Measure"],
        index=["Basic", "Combo_Basic", "C-Value", "Weirdness"]
    )

    # Basic
    print("### Basic : Starting ###")
    res = basic(text, have_single_word=True,
                verbose=True).sort_values(ascending=False)
    res = res[res > 0].index.str.lower().to_list()
    score.loc["Basic", ] = prf_score(res, annotation)
    print("### Basic : Done ###\n\n### Combo Basic : Starting ###")
    # Combo Basic
    res = combo_basic(text, have_single_word=True,
                      verbose=True).sort_values(ascending=False)
    res = res[res > 0].index.str.lower().to_list()
    score.loc["Combo_Basic", ] = prf_score(res, annotation)
    print("### Combo Basic : Done ###\n\n### C-Value : Starting ###")
    # C-Value
    res = cvalues(text, have_single_word=True,
                  verbose=True).sort_values(ascending=False)
    res = res[res > 0].index.str.lower().to_list()
    score.loc["C-Value", ] = prf_score(res, annotation)
    print("### C-Value : Done ###\n\n### Weirdness : Starting ###")
    # Weirdness
    res = weirdness(text, general, verbose=True).sort_values(ascending=False)
    res = res[res > 0].index.str.lower().to_list()
    score.loc["Weirdness", ] = prf_score(res, annotation)
    print("### Weirdness ###")

    return score
