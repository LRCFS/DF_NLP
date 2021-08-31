#!/usr/bin/env python3
"""Benchmark several ATE method for the SemEval 2017 corpus."""

import os
import pandas as pd
from typing import Dict, List, Tuple
from pyate import basic, combo_basic, cvalues, weirdness


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
            df = df.loc[~df.loc[:, "Type"].str.startswith("R"), ]
            ann[uuid] = df
        else:
            raise SyntaxError(f"Unhandled extension: {f_name}")

    return (text, ann)
