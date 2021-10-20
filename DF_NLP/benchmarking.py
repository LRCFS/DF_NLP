#!/usr/bin/env python3
"""Benchmark several ATE method for the SemEval 2017 corpus."""

import argparse
import os
import re
import sys
from math import pow
from typing import Dict, List, Tuple, NoReturn

import numpy as np
import pandas as pd
import spacy
from matplotlib import pyplot
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, precision_recall_curve
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from DF_NLP import ate


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

    nlp = ate.setup_spacy(True)

    text = []
    df = pd.DataFrame(columns=["Type", "Info", "Term"])
    for f_name in tqdm(file_list):
        # Extract strings from the .txt files
        if f_name.endswith(".txt"):
            with open(f_name, "r") as f:
                doc = ate.text_process(nlp, f.read(), True)
            text.append(doc.translate(to_remove))
        # Extract annotation as DataFrame from the .ann files
        elif f_name.endswith(".ann"):
            tmp = pd.read_csv(f_name, names=["Type", "Info", "Term"],
                              sep="\t", dtype=str)
            df = df.append(tmp, ignore_index=True)
        else:
            raise SyntaxError(f"Unhandled extension: {f_name}")

    # Remove row which are not terms and duplicates
    df = df.loc[df.loc[:, "Type"].str.startswith("T"), ]
    df = df.drop_duplicates("Term")
    # Lemmatize
    df.loc[:, "Term"] = df.loc[:, "Term"].apply(
        lambda x: ate.text_process(nlp, x, True)
    )

    annotation = df.loc[:, "Term"].to_list()
    annotation = [a.translate(to_remove) for a in annotation if a]

    return (text, annotation)


def _prf_score(candidate: List[str], annotation: List[str],
               beta: int = 1) -> Dict[str, float]:
    """Compute the precision, recall and F-measure for the candidate terms.

    Args:
        candidate: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.
        beta: Parameter of F-Measure and allowing to give more
            importance to precision (<1) or to recall (>1).

    Returns:
        A dictionnary containing the precision, the recall and F-measure.
    """
    print("PRF scoring...")
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


def _pak_score(candidate: List[str], annotation: List[str],
               k_rank: List[int] = [500, 1000, 5000]) -> Dict[str, float]:
    """Compute the Precision@K feature for the candidate terms.

    Args:
        candidate: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.
        k_rank: List of K rank(s) to compute Precision@K.

    Returns:
        A dictionnary containing the Precision@K for one or more K rank(s).
    """
    print("Precision@K scoring...")

    score = {}
    for k in k_rank:
        sub = candidate[0:k]
        match = sum(c in sub for c in annotation)
        try:
            score[f"Precision@{k}"] = match / len(sub)
        except ZeroDivisionError:
            score[f"Precision@{k}"] = 0.0

    print(score)
    return score


def _bpref_score(candidate: List[str],
                 annotation: List[str]) -> Dict[str, float]:
    """Compute the Bpref feature for the candidate terms.

    Args:
        candidate: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.

    Returns:
        A dictionnary containing the bpref.
    """
    print("Bpref scoring...")

    total = 0
    match = sum(c in candidate for c in annotation)
    ann_index = [candidate.index(ann) for ann in annotation
                 if ann in candidate]

    total = sum(
        1 - len(list(set(candidate[0:i]) - set(annotation))) / len(candidate)
        for i in tqdm(ann_index)
    )
    try:
        score = {"Bpref": (1/match) * total}
    except ZeroDivisionError:
        score = {"Bpref": 0.0}

    print(score)
    return score


def _scoring(method: str, candidate: List[str], annotation: List[str],
             beta: int = 1,
             k_rank: List[int] = [500, 1000, 5000]) -> Dict[str, float]:
    """Compute the Precision@K feature for the candidate terms.

    Args:
        method: The scoring method: 'PRF' for Precision, Recall
            and F-measure; 'P@K' for Precision@K and 'Bpref' for Bpref.
        candidate: Candidate terms identified by an ATE method.
        annotation: Correct terms annotated by authors.
        beta: = Parameter of F-Measure and allowing to give more
            importance to precision (<1) or to recall (>1).
        k_rank: List of K rank(s) to compute Precision@K.

    Returns:
        A dictionnary containing the score feature(s) results.
    """
    if method == "PRF":
        return _prf_score(candidate, annotation, beta)
    elif method == "P@K":
        return _pak_score(candidate, annotation, k_rank)
    else:
        return _bpref_score(candidate, annotation)


def pr_curve(candidates: pd.Series, annotation: List[str],
             ate: str, path: str) -> NoReturn:
    """Write a Precision-Recall curve plot and return the best threshold.

    Args:
        candidates: List of extracted terms from an ATE method to
            benchmark.
        annotation: The terms identified by the authors.
        ate: ATE method used
        path: Directory where the plot should be saved.
    """
    # Clear plot
    pyplot.clf()
    pyplot.figure(figsize=(6, 6))

    y = [1 if c in annotation else 0 for c in candidates.index]
    scores = candidates.values

    # Computing PRF
    precision, recall, _ = precision_recall_curve(y, scores)
    # Compute AUC
    auc_val = round(auc(recall, precision), 2)
    # Plot the precision-recall curves
    pyplot.plot([0, 1], [1, 0], linestyle="--", color="red",
                label="Random", zorder=0)
    pyplot.plot(recall, precision, marker=".", color="royalblue",
                label=f"{ate} (AUC={auc_val})", zorder=-1)

    # Axis labels
    pyplot.xlabel("Recall")
    pyplot.ylabel("Precision")
    pyplot.title(f"Precision-Recall curve for {ate}")
    # Axis limit
    pyplot.xlim(0.0, 1.0)
    pyplot.ylim(0.0, 1.0)
    # Show the legend
    pyplot.legend()
    # Save the plot
    pyplot.savefig(os.path.join(path, f"{ate}.png"))


def benchmarck(text: List[str], annotation: List[str], path: str,
               method: str = "PRF", beta: int = 1,
               k_rank: List[int] = [500, 1000, 5000]) -> pd.DataFrame:
    """Benchmark Basic, Combo Basic, C-Value and Weirdness ATE methods.

    Args:
        text: The corpus used to compare the methods.
        annotation: The terms identified by authors in `text`.
        path: Directory where the plots should be saved.
        method: The scoring method: 'PRF' for Precision, Recall
            and F-measure; 'P@K' for Precision@K and 'Bpref' for Bpref.
        beta: Parameter of F-Measure (PRF) and allowing to give more
            importance to precision (<1) or to recall (>1).
        k_rank: List of K rank(s) to compute Precision@K.

    Returns:
        DataFrame containing precision, recall and F-measure for each
        method.

    Raises:
        ValueError: If at least one `k_rank` is invalid.
        ValueError: If the scoring `method` is unknown.
    """
    # Check validity of k rank(s)
    if (any(k <= 0 for k in k_rank)
            or any(not isinstance(k, int) for k in k_rank)):
        raise ValueError("K rank(s) contains a value <= 0 or a non int value!")

    if method == "PRF":
        col = ["Precision", "Recall", "F_Measure"]
    elif method == "P@K":
        col = [f"Precision@{k}" for k in k_rank]
    elif method == "Bpref":
        col = ["Bpref"]
    else:
        raise ValueError(f"Unknown scoring method: {method}")

    score = pd.DataFrame(columns=col, index=[
        "Basic", "Combo_Basic", "C-Value", "Weirdness"])

    # Basic
    print("### Basic : Starting ###")
    res = ate.run_ate("Basic", True, text)
    pr_curve(res, annotation, "Basic", path)
    res = res.index.to_list()
    score.loc["Basic", ] = _scoring(method, res, annotation, beta, k_rank)
    print("### Basic : Done ###\n\n### Combo Basic : Starting ###")
    # Combo Basic
    res = ate.run_ate("Combo", True, text)
    pr_curve(res, annotation, "Combo_Basic", path)
    res = res.index.to_list()
    score.loc["Combo_Basic", ] = _scoring(method, res, annotation, beta,
                                          k_rank)
    print("### Combo Basic : Done ###\n\n### C-Value : Starting ###")
    # C-Value
    res = ate.run_ate("Cvalue", True, text)
    pr_curve(res, annotation, "C-Value", path)
    res = res.index.to_list()
    score.loc["C-Value", ] = _scoring(method, res, annotation, beta, k_rank)
    print("### C-Value : Done ###\n\n### Weirdness : Starting ###")
    # Weirdness
    res = ate.run_ate("Weirdness", True, text)
    pr_curve(res, annotation, "Weirdness", path)
    res = res.index.to_list()
    score.loc["Weirdness", ] = _scoring(method, res, annotation, beta, k_rank)
    print("### Weirdness ###")

    return score


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("input", type=str, help="Path to the input directory")
    cli.add_argument("output", type=str, help="Path to the output directory")
    cli.add_argument("--scoring", nargs="*", type=str, default=["PRF"],
                     choices=["PRF", "P@K", "Bpref"],
                     help="The scoring methods to use")
    cli.add_argument("--beta", type=float, default=1, help="Parameter of \
F-Measure and allowing to give more importance to precision (<1) or to \
recall (>1).")
    cli.add_argument("--ranks", nargs="*", type=int, default=[500, 1000, 5000],
                     help="The ranks to compute for P@K")

    args = cli.parse_args()

    text, ann = read_files(args.input)
    for s in args.scoring:
        score = benchmarck(text, ann, args.output, method=s, beta=args.beta,
                           k_rank=args.ranks)
        filename = os.path.join(args.output, f"score_{s}.csv")
        score.to_csv(filename, sep=";")
