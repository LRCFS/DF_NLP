"""Module handling requests to API."""

import json
import sys
import xml.etree.ElementTree as ET
from typing import Union

import requests


def _get(query: str) -> requests.Response:
    """Send a request and return the API response.

    Args:
        query: Request to send.

    Returns:
        API response to the request.
    """
    resp = requests.get(query)
    if resp.status_code != 200:
        raise Exception(f"Error with the following request: {query}\n"
                        + f"HTTP status code: {resp.status_code}")

    return resp


def elsevier_get(doi: str, api_key: str) -> str:
    """Query information through a DOI to Elsevier.

    Args:
        doi: Requested DOI.
        api_key: Key authorizing access to Elsevier's API.

    Returns:
        Elsevier's API answer as a string.
    """
    query = ("https://api.elsevier.com/content/article/doi/"
             + f"{doi}?APIKey={api_key}")

    return _get(query).content.decode("UTF-8")


def springer_get(doi: str, api_key: str) -> str:
    """Query information through a DOI to Springer.

    Args:
        doi: Requested DOI.
        api_key: Key authorizing access to Springer's API.

    Returns:
        Springer's API answer as a string.
    """
    oa_query = ("http://api.springernature.com/openaccess/jats/doi/"
                + f"{doi}?api_key={api_key}")
    oa_resp = _get(oa_query).content.decode("UTF-8")
    root = ET.fromstring(oa_resp)
    oa_nb_result = int(root.find("./result/total").text)

    if not oa_nb_result:
        meta_query = ("http://api.springernature.com/meta/v2/jats?q=doi:"
                      + f"{doi}&api_key={api_key}")
        return _get(meta_query).content.decode("UTF-8")
    return oa_resp


def ieee_get_meta(doi: str, api_key: str) -> str:
    """Query metadata through a DOI to IEEE.

    Args:
        doi: Requested DOI.
        api_key: Key authorizing access to IEEE's API.

    Returns:
        IEEE's API answer as a string.
    """
    query = ("http://ieeexploreapi.ieee.org/api/v1/search/articles?"
             + f"apikey={api_key}&doi={doi}&format=xml")

    return _get(query).content.decode("UTF-8", "ignore")


def ieee_get_oa(meta: str, api_key: str) -> str:
    """Query open access view to IEEE using the metadata answer.

    Args:
        meta: Metada answer.
        api_key: Key authorizing access to IEEE's API.

    Returns:
        IEEE's API answer as a string.
    """
    root = ET.fromstring(meta)
    art_number = root.find("./article/article_number").text

    query = ("http://ieeexploreapi.ieee.org/api/v1/search/document/"
             + f"{art_number}/fulltext?apikey={api_key}&format=xml")
    return _get(query).content.decode("UTF-8", "ignore")


def api_keys(api_keys_path: str) -> dict:
    """Check the presence and status of all API keys before retrieving it.

    Args:
        api_keys_path: Path to the file containings API keys.

    Returns:
        Dictionnary containing all API keys.
    """
    with open(api_keys_path, "r") as f:
        keys = json.load(f)

    # Elsevier API key
    try:
        elsevier_get("10.1016/j.ibusrev.2010.09.002", keys["elsevier"])
        print("Elsevier API key status: OK")
    except Exception:
        print("An issue occured while checking Elsevier API")
        sys.exit(1)

    # Springer API key
    try:
        springer_get("10.1007/s11276-008-0131-4", keys["springer"])
        print("Springer API key status: OK")
    except Exception:
        print("An issue occured while checking Springer API")
        sys.exit(1)

    # IEEE API key
    try:
        ieee_get_meta("10.1109/ACCESS.2020.2979348", keys["ieee"])
        print("IEEE API key status: OK")
    except Exception:
        print("An issue occured while checking IEEE API")
        sys.exit(1)

    return keys
