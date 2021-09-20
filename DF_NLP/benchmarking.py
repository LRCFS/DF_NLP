#!/usr/bin/env python3
"""Benchmark several ATE method for the SemEval 2017 corpus."""

import argparse
import os
import sys
from math import pow
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot
from pyate import TermExtraction, basic, combo_basic, cvalues, weirdness
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, auc
from sklearn.model_selection import train_test_split
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
             ate: str, path: str, beta: int = 1) -> float:
    """Write a Precision-Recall curve plot and return the best threshold.

    Args:
        candidates: List of extracted terms from an ATE method to
            benchmark.
        annotation: The terms identified by the authors.
        beta: Parameter of F-Measure and allowing to give more
            importance to precision (<1) or to recall (>1).
        ate: ATE method used
        path: Directory where the plot should be saved.

    Returns
        The best threshold to use according to the chosen value of `beta`.
    """
    # Clear plot
    pyplot.clf()

    x = np.reshape(candidates.values, (len(candidates), 1))
    y = [1 if c in annotation else 0 for c in candidates.index]

    # Split into train/test sets
    xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size=0.5,
                                                    random_state=2)
    # Fit a model
    model = LogisticRegression(solver='lbfgs')
    model.fit(xtrain, ytrain)
    # Predict probabilities
    proba = model.predict_proba(xtest)
    proba = proba[:, 1]
    # Computing PRF
    p, r, thresholds = precision_recall_curve(ytest, proba)
    fmeasure = (1 + pow(beta, 2)) * (p*r / (pow(beta, 2)*p + r))
    # Locate the index of the largest F-Measure
    ix = np.argmax(fmeasure)
    best = round(thresholds[ix], 3)
    auc_val = round(auc(r, p), 2)
    print(f"Best threshold={best}  AUC={auc_val}")
    # Plot the precision-recall curves
    no_skill = len([y for y in ytest if y == 1]) / len(ytest)
    pyplot.plot([0, 1], [no_skill, no_skill], linestyle="--", color="red",
                label="No Skill", zorder=0)
    pyplot.plot(r, p, marker=".", color="royalblue",
                label=f"Logistic (AUC={auc_val})", zorder=-1)
    pyplot.scatter(r[ix], p[ix], marker="o", color="black", label="Best",
                   zorder=1)
    pyplot.annotate(f"Best Threshold = {best}", xy=(r[ix], p[ix]),
                    xytext=(5, 2), textcoords='offset points', ha='right',
                    va='bottom')
    # Axis labels
    pyplot.xlabel("Recall")
    pyplot.ylabel("Precision")
    pyplot.title(f"Precision-Recall curve for {ate} (Beta = {beta})")
    # Show the legend
    pyplot.legend()
    # Save the plot
    pyplot.savefig(os.path.join(path, f"{ate}.png"))

    return best


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
    general = TermExtraction.get_general_domain()

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
    res = basic(text, have_single_word=True,
                verbose=True).sort_values(ascending=False)
    best = pr_curve(res, ann, "Basic", path, beta)
    res = res[res >= best].index.str.lower().to_list()
    score.loc["Basic", ] = _scoring(method, res, annotation, beta, k_rank)
    print("### Basic : Done ###\n\n### Combo Basic : Starting ###")
    # Combo Basic
    res = combo_basic(text, have_single_word=True,
                      verbose=True).sort_values(ascending=False)
    best = pr_curve(res, ann, "Combo_Basic", path, beta)
    res = res[res >= best].index.str.lower().to_list()
    score.loc["Combo_Basic", ] = _scoring(method, res, annotation, beta,
                                          k_rank)
    print("### Combo Basic : Done ###\n\n### C-Value : Starting ###")
    # C-Value
    res = cvalues(text, have_single_word=True,
                  verbose=True).sort_values(ascending=False)
    best = pr_curve(res, ann, "C-Value", path, beta)
    res = res[res >= best].index.str.lower().to_list()
    score.loc["C-Value", ] = _scoring(method, res, annotation, beta, k_rank)
    print("### C-Value : Done ###\n\n### Weirdness : Starting ###")
    # Weirdness
    res = weirdness(text, general, verbose=True).sort_values(ascending=False)
    best = pr_curve(res, ann, "Weirdness", path, beta)
    res = res[res >= best].index.str.lower().to_list()
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
