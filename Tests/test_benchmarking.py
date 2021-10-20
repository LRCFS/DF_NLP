"""Tests the benchmarking.py functions"""

import pytest
from DF_NLP import benchmarking as bm

import fixture


@pytest.mark.parametrize("param", [
    {"in": ["a", "b", "c", "d", "e", "f"], "out":{
        "Precision": 1/3, "Recall": 1.0, "F_Measure": 0.5}},
    {"in": ["c"], "out":{
        "Precision": 1.0, "Recall": 0.5, "F_Measure": 2/3}},
    {"in": ["c", "e"], "out":{
        "Precision": 1.0, "Recall": 1.0, "F_Measure": 1.0}},
    {"in": ["a", "b", "d", "e", "f"], "out":{
        "Precision": 0.2, "Recall": 0.5, "F_Measure": 0.28571428571428575}},
    {"in": ["a", "b", "d", "f"], "out":{
        "Precision": 0.0, "Recall": 0.0, "F_Measure": 0.0}},
])
def test_prf_score(param):
    """Test that _prf_score() return the right value"""
    assert bm._prf_score(param.get("in"), ["c", "e"]) == param.get("out")


@pytest.mark.parametrize("param", [
    {"in": ["a", "b", "c", "d", "e", "f"], "out":{
        "Precision@0": 0.0, "Precision@1": 0.0, "Precision@4": 0.25}},
    {"in": ["c"], "out":{
        "Precision@0": 0.0, "Precision@1": 1.0, "Precision@4": 1.0}},
    {"in": ["c", "e"], "out":{
        "Precision@0": 0.0, "Precision@1": 1.0, "Precision@4": 1.0}},
    {"in": ["a", "b", "d", "e", "f"], "out":{
        "Precision@0": 0.0, "Precision@1": 0.0, "Precision@4": 0.25}},
    {"in": ["a", "b", "d", "f"], "out":{
        "Precision@0": 0.0, "Precision@1": 0.0, "Precision@4": 0.0}},
])
def test_pak_score(param):
    """Test that _pak_score() return the right value"""
    assert bm._pak_score(param.get("in"), ["c", "e"],
                         [0, 1, 4]) == param.get("out")


@pytest.mark.parametrize("param", [
    {"in": ["a", "b", "c", "d", "e", "f"], "out":{"Bpref": 7/12}},
    {"in": ["c"], "out":{"Bpref": 1.0}},
    {"in": ["c", "e"], "out":{"Bpref": 1.0}},
    {"in": ["a", "b", "d", "e", "f"], "out":{"Bpref": 0.4}},
    {"in": ["a", "b", "d", "f"], "out":{"Bpref": 0.0}}
])
def test_bpref_score(param):
    """Test that _bpref_score() return the right value"""
    assert bm._bpref_score(param.get("in"), ["c", "e"]) == param.get("out")
