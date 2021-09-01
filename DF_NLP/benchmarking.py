#!/usr/bin/env python3
"""Benchmark several ATE method for the SemEval 2017 corpus."""

import os
from math import pow
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from pyate import TermExtraction, basic, combo_basic, cvalues, weirdness
from tqdm import tqdm


def read_files(directory: str) -> Tuple[Dict]:
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

    text = {}
    ann = {}
    for f_name in file_list:
        uuid, _ = os.path.basename(f_name).split(".")
        # Extract strings from the .txt files
        if f_name.endswith(".txt"):
            with open(f_name, "r") as f:
                text[uuid] = f.read()
        # Extract annotation as DataFrame from the .ann files
        elif f_name.endswith(".ann"):
            df = pd.read_csv(f_name, header=0,
                             names=["Type", "Info", "Term"],
                             sep="\t", dtype=str)
            # Remove rows which are not identified terms
            df = df.loc[df.loc[:, "Type"].str.startswith("T"), ]
            df.loc[:, "Term"] = df.loc[:, "Term"].str.lower()
            df = df.drop_duplicates("Term")
            ann[uuid] = df
        else:
            raise SyntaxError(f"Unhandled extension: {f_name}")

    return (text, ann)


def PRF_score(candidates: List[str], annotation: List[str]) -> Tuple[float]:
    """Method which compute the precision, recall and F-measure.

    Args:
        candidates: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.

    Returns:
        A tuple containing the precision, the recall and F-measure.
    """
    beta = 2
    match = 0
    for c in candidates:
        if c in annotation:
            match += 1

    precision = match / len(candidates)
    recall = match / len(annotation)
    f_measure = (1 + pow(beta, 2)) * (precision * recall /
                                      (pow(beta, 2) * precision + recall))

    return (precision, recall, f_measure)
